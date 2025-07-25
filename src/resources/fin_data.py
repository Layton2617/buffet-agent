import yfinance as yf
import finnhub
import os
import dotenv
import pandas as pd
import requests
import time
import json
from datetime import datetime
import numpy as np
import sys
from src.financial_tools import FinancialTools
from tqdm import tqdm

class MultiDataAgent:
    """
    多数据源抓取与管理，支持yfinance、finnhub、simfin等。
    """
    def __init__(self, finnhub_key=None):
        # 初始化API密钥和客户端
        self.finnhub_key = finnhub_key
        self.finnhub_client = finnhub.Client(api_key=self.finnhub_key) if self.finnhub_key else None
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        
    def _check_yfinance_ticker(self, tickers: list[str], start_date: str, end_date: str) -> dict[str, pd.DataFrame]:
        """
        批量获取yfinance的公司信息和历史行情。
        """
        print("yfinance".center(50, "="), file=sys.stderr)
        stocks = yf.Tickers(tickers)
        infos = {item: stocks.tickers[item].info for item in tickers}
        print("infos fetched")

        missed = []
        for item in tickers:
            if item not in infos:
                missed.append(item)
        if len(missed) > 0:
            print(f"Ticker {missed} not found in yfinance.", file=sys.stderr)
        else:
            print("All tickers found in yfinance.", file=sys.stderr)

        # 获取历史行情数据
        hist = stocks.history(start=start_date, end=end_date, period=None)
        print("Price history fetched", file=sys.stderr)
        # 调整多重索引格式，便于后续处理
        columns = map(lambda x: (x[1], x[0]), hist.columns)
        hist.columns = pd.MultiIndex.from_tuples(sorted(columns, key=lambda x: x[0]))
        return {'company_info': infos, 'company_history': {item: hist[item] for item in tickers}}
    
    def get_portfolio_analysis_metrics(self, tickers: list[str]) -> dict:
        """
        通过yfinance获取股票的财务指标。
        """
        target_metrics = [
            "returnOnEquity",
            "debtToEquity",
            "profitMargins",
            "revenueGrowth",
            "trailingPE"
        ]
        results = []
        for ticker in tickers:
            ticker_info = yf.Ticker(ticker).info
            for metric in target_metrics:
                if metric in ticker_info:
                    results.append({ticker: {metric: ticker_info[metric]}})
        return results
    
    def get_tickers_fcf(self, tickers: list[str]) -> dict:
        """
        获取股票的自由现金流。
        """
        results = dict()
        for ticker in tickers:
            ticker_info = yf.Ticker(ticker).info
            results[ticker] = ticker_info.get("freeCashflow", 0)
        return results
    
    def get_tickers_pe(self, tickers: list[str]) -> dict:
        """
        获取股票的市盈率。
        """
        results = dict()
        for ticker in tickers:
            ticker_info = yf.Ticker(ticker).info
            results[ticker] = ticker_info.get("trailingPE", 0)
        return results
    
    def get_tickers_earnings_growth(self, tickers: list[str]) -> dict:
        """
        获取股票的盈利增长率。
        """
        results = dict()
        for ticker in tickers:
            ticker_info = yf.Ticker(ticker).info
            results[ticker] = ticker_info.get("earningsGrowth", 0)
        return results
    
    def get_tickers_peers(self, tickers: list[str]) -> dict:
        """
        获取股票的同行。
        """
        peers = {ticker: self.finnhub_client.company_peers(symbol=ticker) for ticker in tickers}
        return peers

    def get_tickers_average_peers_pe(self, tickers: list[str]) -> dict:
        """
        获取每个ticker的同行公司平均市盈率（trailingPE）。
        先通过get_tickers_peers获取同行列表，再抓取每个同行的trailingPE，求均值。
        用于补全行业平均PE（industry_avg_pe）字段。
        """
        results = dict()
        peers = self.get_tickers_peers(tickers)
        for ticker, peers in peers.items():
            store = []
            for peer in peers:
                if ticker != peer:
                    store.append(yf.Ticker(peer).info.get("trailingPE", 0))
            # 过滤掉为0的PE，避免极端值影响
            valid_pe = [pe for pe in store if pe > 0]
            results[ticker] = round(sum(valid_pe) / len(valid_pe), 2) if valid_pe else None
        return results
    
    def get_tickers_historical_pe_range(self, tickers: list[str], years: int = 10) -> dict:
        """
        获取每个ticker的历史PE区间（min, max, mean, list of yearly PE）。
        - EPS数据用Alpha Vantage
        - 价格数据用yfinance，3个月interval，按年聚合
        """
        pe_results = {}

        for ticker in tickers:
            # 1. 获取历史EPS
            url = f'https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={self.alpha_vantage_key}'
            response = requests.get(url)
            data = response.json()
            eps_dict = {}
            for item in data.get("annualEarnings", []):
                year = item["fiscalDateEnding"][:4]
                try:
                    eps = float(item["reportedEPS"])
                    eps_dict[year] = eps
                except Exception:
                    continue

            # 2. 获取历史价格（3个月interval，近years年）
            end = datetime.now()
            start = datetime(end.year - years, 1, 1)
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start, end=end, interval="3mo")
            if hist.empty:
                pe_results[ticker] = {"error": "No price data"}
                continue

            # 3. 按年聚合均价
            hist["year"] = hist.index.year
            yearly_mean_price = hist.groupby("year")["Close"].mean().to_dict()

            # 4. 计算每年PE
            yearly_pe = []
            for year, eps in eps_dict.items():
                year_int = int(year)
                if year_int in yearly_mean_price and eps and eps != 0:
                    pe = yearly_mean_price[year_int] / eps
                    yearly_pe.append(pe)

            if yearly_pe:
                pe_results[ticker] = {
                    "min": round(min(yearly_pe), 2),
                    "max": round(max(yearly_pe), 2),
                    "mean": round(sum(yearly_pe) / len(yearly_pe), 2),
                    "yearly_pe": [round(item, 2) for item in yearly_pe]
                }
            else:
                pe_results[ticker] = {"error": "No valid PE data"}

        return pe_results

    def get_pe_analysis_inputs_for_tickers(self, tickers: list[str], years: int = 10) -> dict:
        """
        为每个ticker准备analyze_pe_ratio所需的参数：
        - current_pe: 当前市盈率（用yfinance info['trailingPE']）
        - industry_avg_pe: 行业平均市盈率（用yfinance info['industryPE']，如无则用所有ticker均值）
        - historical_pe_range: 历史PE区间（用get_tickers_historical_pe_range）
        - earnings_growth_rate: 盈利增长率（用get_tickers_earnings_growth）
        返回：{ticker: {current_pe, industry_avg_pe, historical_pe_range, earnings_growth_rate}}
        """
        print(f"[get_pe_analysis_inputs_for_tickers] 输入tickers: {tickers}", file=sys.stderr)
        pe_inputs = {}
        ticker_infos = {ticker: yf.Ticker(ticker).info for ticker in tqdm(tickers, desc="抓取yfinance info", file=sys.stderr)}
        historical_pe = self.get_tickers_historical_pe_range(tickers, years=years)
        earnings_growth = self.get_tickers_earnings_growth(tickers)
        industry_pes = [info.get('industryPE') for info in ticker_infos.values() if info.get('industryPE')]
        avg_industry_pe = float(np.mean(industry_pes)) if industry_pes else None
        peers_avg_pe = self.get_tickers_average_peers_pe(tickers)
        for ticker in tqdm(tickers, desc="聚合PE数据", file=sys.stderr):
            info = ticker_infos.get(ticker, {})
            current_pe = info.get('trailingPE')
            industry_avg_pe = info.get('industryPE') or peers_avg_pe.get(ticker) or avg_industry_pe
            hist_pe_data = historical_pe.get(ticker, {})
            historical_pe_range = hist_pe_data.get('yearly_pe') if isinstance(hist_pe_data, dict) else None
            earnings_growth_rate = earnings_growth.get(ticker, 0)
            missing = []
            if not current_pe:
                missing.append('current_pe')
            if not industry_avg_pe:
                missing.append('industry_avg_pe')
            if not historical_pe_range:
                missing.append('historical_pe_range')
            print(f"[get_pe_analysis_inputs_for_tickers] {ticker}: current_pe={current_pe}, industry_avg_pe={industry_avg_pe}, historical_pe_range={historical_pe_range}, earnings_growth_rate={earnings_growth_rate}, missing={missing}", file=sys.stderr)
            if not missing or (current_pe and historical_pe_range):
                pe_inputs[ticker] = {
                    'current_pe': current_pe,
                    'industry_avg_pe': industry_avg_pe,
                    'historical_pe_range': historical_pe_range,
                    'earnings_growth_rate': earnings_growth_rate,
                }
            else:
                pe_inputs[ticker] = {'error': f"Missing data: {', '.join(missing)}"}
        return pe_inputs

    def get_tickers_margin_safety(self, tickers: list[str]) -> dict:
        """
        计算每个ticker的安全边际（Margin of Safety）。
        步骤：
        1. 获取当前股价（currentPrice）
        2. 获取自由现金流（freeCashflow）
        3. 用DCF方法估算企业价值
        4. 计算安全边际 = (DCF估值 - 当前股价) / 当前股价
        返回：{ticker: {"dcf_value": DCF估值, "current_price": 当前股价, "margin_safety": 安全边际}}
        """
        print(f"[get_tickers_margin_safety] 输入tickers: {tickers}", file=sys.stderr)
        print("-"*50, file=sys.stderr)
        results = {}
        for ticker in tqdm(tickers, desc="安全边际每个ticker", file=sys.stderr):
            info = yf.Ticker(ticker).info
            shares_outstanding = info.get("sharesOutstanding")
            current_price = info.get("currentPrice")
            fcf = info.get("freeCashflow")
            if not current_price or not fcf:
                print(f"[get_tickers_margin_safety] {ticker} 缺少currentPrice或freeCashflow数据", file=sys.stderr)
                print(info, file=sys.stderr)
                results[ticker] = {"error": "缺少currentPrice或freeCashflow数据"}
                continue
            dcf_result = FinancialTools.simple_gordon_dcf(
                FCF0=fcf,
                growth_rate=0.025,
                discount_rate=0.10
            )
            dcf_value = dcf_result.get("DCF")
            if not dcf_value:
                print(f"[get_tickers_margin_safety] {ticker} DCF估值计算失败", file=sys.stderr)
                print(dcf_result, file=sys.stderr)
                results[ticker] = {"error": "DCF估值计算失败"}
                continue
            intrinsic_value_per_share = dcf_value / shares_outstanding
            # margin_safety = round((intrinsic_value_per_share - current_price) / intrinsic_value_per_share, 4)
            print(f"[get_tickers_margin_safety] {ticker}: dcf_value|intrinsic_value={intrinsic_value_per_share}, current_price={current_price}", file=sys.stderr)
            print("-"*50, file=sys.stderr)
            results[ticker] = {
                "intrinsic_value": round(intrinsic_value_per_share, 2),
                "current_price": current_price,
                # "margin_safety": margin_safety
            }
        return results

    def _check_finnhub_ticker(self, tickers: list[str], start_date: str, end_date: str, limit: int = 3) -> dict[str, dict]:
        """
        批量获取finnhub的公司信息、新闻、财务等。
        """
        print("finnhub".center(50, "="), file=sys.stderr)
        # 公司基本信息
        profiles = [self.finnhub_client.company_profile2(symbol=item) for item in tickers]
        print("company_profile fetched", file=sys.stderr)
        # 新闻
        company_news = {item: self.finnhub_client.company_news(symbol=item, _from=start_date, to=end_date)[:limit] for item in tickers}
        print("company_news fetched", file=sys.stderr)
        time.sleep(1.5)
        # 内部人情绪
        # insider_sentiment = {item: self.finnhub_client.stock_insider_sentiment(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers}
        # print("insider_sentiment fetched")
        time.sleep(1.5)
        # 政府支出
        # usa_spending = {item: self.finnhub_client.stock_usa_spending(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers}
        # print("usa_spending fetched")
        time.sleep(1.5)
        # 游说活动
        # lobbying = {item: self.finnhub_client.stock_lobbying(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers}
        # print("lobbying fetched")
        time.sleep(1.5)
        # 签证申请
        # visa_application = {item: self.finnhub_client.stock_visa_application(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers}
        # print("visa_application fetched")
        time.sleep(1.5)
        # 专利
        # uspto_patents = {item: self.finnhub_client.stock_uspto_patent(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers}
        # print("uspto_patents fetched")
        time.sleep(1.5)
        # 盈利意外
        # earning_suprice = {item: self.finnhub_client.company_earnings(symbol=item, limit=limit) for item in tickers}
        # print("earning_suprice fetched")
        # 返回所有抓取结果
        return profiles, company_news

    def get_news_from_finnhub(self, tickers: list[str], start_date: str, end_date: str, limit: int = 10) -> dict[str, dict]:
        """
        批量获取finnhub的新闻。
        """
        _, company_news = self._check_finnhub_ticker(tickers, start_date, end_date, limit)
        new_template = "{ticker} on {date} with '{headline}': '{summary}'"
        news = []
        for ticker, news_list in company_news.items():
            for news_item in news_list:
                news.append(new_template.format(ticker=ticker, date=datetime.fromtimestamp(news_item.get("datetime")).strftime("%Y-%m-%d"), headline=news_item.get("headline"), summary=news_item.get("summary")))
        return news

    def _check_simfin_ticker(self, tickers: list[str], start_date: str, end_date: str) -> list[dict]:
        """
        批量获取simfin的公司财报。
        """
        print("simfin".center(50, "="), file=sys.stderr)
        if not start_date and not end_date:
            raise ValueError("Start and end date are required.")

        url = "https://backend.simfin.com/api/v3/companies/statements/compact?ticker={tickers}&statements=PL,BS,CF,DERIVED&start={start}&end={end}&details=false"
        headers = {
            "accept": "application/json",
            "Authorization": os.getenv('AUTHORIZATION')
        }
        url_format = url.format(tickers=",".join(tickers), start=start_date, end=end_date)
        response = requests.get(url_format, headers=headers)
        assert response.status_code == 200, f"Failed to fetch data from SimFin.\n{response.status_code}\n{response.text}"
        results = response.json()
        print("simfin results fetched", file=sys.stderr)
        return results
    
    def _simfin_data_extraction(self, data: list[dict]) -> dict:
        """
        提取自由现金流。
        """
        reported_date_index = None
        free_cash_flow_index = None
        earnings_per_share_index = None

        tickers_results = {ticker_info.get("ticker"): ticker_info.get("statements") for ticker_info in data}
        free_cash_flow = {ticker: [] for ticker in tickers_results.keys()}
        earnings_per_share = {ticker: [] for ticker in tickers_results.keys()}
        for key, value in tickers_results.items():
            for index, column in enumerate(value[3].get("columns")):
                if "Free Cash Flow" == column:
                    free_cash_flow_index = index
                if "Earnings Per Share, Diluted" == column:
                    earnings_per_share_index = index
                if "Report Date" == column:
                    reported_date_index = index

            for item in value[3].get("data"):
                free_cash_flow[key].append((item[reported_date_index], item[free_cash_flow_index]))
                earnings_per_share[key].append((item[reported_date_index], item[earnings_per_share_index]))

        return free_cash_flow, earnings_per_share


    def free_cash_flow_and_earnings_per_share(self,   tickers: list[str], start_date: str, end_date: str) -> dict:
        results = self._check_simfin_ticker(tickers, start_date, end_date)

        # 提取不同的自由现金流和每股收益
        free_cash_flow, earnings_per_share = self._simfin_data_extraction(results)
        return free_cash_flow, earnings_per_share
        
    
    def _fetching_yfinance_ticker(self, tickers: list[str], start_date: str, end_date: str, dir: str = "yfinance_results"):
        """
        抓取yfinance数据并保存本地。
        """
        yf_results = self._check_yfinance_ticker(tickers, start_date, end_date)
        if not os.path.exists(dir):
            os.mkdir(dir)
        # 保存公司信息
        with open(f"{dir}/company_info.json", "w") as f:
            json.dump(yf_results.get('company_info'), f, indent=2)
        # 保存历史行情
        for ticker in tickers:
            hist = yf_results.get('company_history').get(ticker)
            if hist is not None:
                hist.to_csv(f"{dir}/{ticker}_history.csv")
        print("yfinance results saved.", file=sys.stderr)

    def _fetching_finnhub_ticker(self, tickers: list[str], start_date: str, end_date: str, dir: str = "finnhub_results"):
        """
        抓取finnhub数据并保存本地。
        """
        finnhub_results = self._check_finnhub_ticker(tickers, start_date, end_date)
        if not os.path.exists(dir):
            os.mkdir(dir)
    
        for key, value in finnhub_results.items():
            if key == "company_profile":
                # 公司信息为列表，直接存为 csv
                target = pd.DataFrame(value).to_csv(f"{dir}/{key}.csv")
                continue
            for ticker in tickers:
                try:
                    target = value.get(ticker)
                    df = pd.DataFrame(target)
                    df.to_csv(f"{dir}/{key}_{ticker}.csv")
                except Exception as e:
                    print(f"[finnhub] Error: {key} - {ticker} - {e}", file=sys.stderr)
        print("finnhub results saved.", file=sys.stderr)

    def _fetching_simfin_ticker(self, tickers: list[str], start_date: str, end_date: str, dir: str = "simfin_results"):
        """
        抓取simfin数据并保存本地。
        """
        simfin_results = self._check_simfin_ticker(tickers, start_date, end_date)
        if not os.path.exists(dir):
            os.mkdir(dir)
        with open(f"{dir}/simfin_results.json", "w") as f:
            json.dump(simfin_results, f, indent=2, ensure_ascii=False)
        print("simfin results saved.", file=sys.stderr)

    def fetching_all_ticker(self, tickers: list[str], start_date: str, end_date: str, dir: str = "results"):
        """
        一键抓取所有数据源的数据并保存。
        """
        if not os.path.exists(dir):
            os.mkdir(dir)
        dir_yfinance = os.path.join(dir, "yfinance_results")
        dir_finnhub = os.path.join(dir, "finnhub_results")
        dir_simfin = os.path.join(dir, "simfin_results")
        self._fetching_yfinance_ticker(tickers, start_date, end_date, dir_yfinance)
        self._fetching_finnhub_ticker(tickers, start_date, end_date, dir_finnhub)
        self._fetching_simfin_ticker(tickers, start_date, end_date, dir_simfin)



# 用法示例
# result = get_tickers_historical_pe_range(["AAPL", "MSFT"])
# print(result)

if __name__ == "__main__":
    print("=== MultiDataAgent 基本连接和 ticker 检查 ===")
    dotenv.load_dotenv()
    FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', "d1srh21r01qhe5rblou0d1srh21r01qhe5rbloug")

    agent = MultiDataAgent(FINNHUB_API_KEY)
    tickers = ['AAPL', 'MSFT']
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    dir_ = "results"

    print(agent.get_tickers_margin_safety(tickers))