import yfinance as yf
import finnhub
import os
import dotenv
import pandas as pd
import requests
import time
import json

class MultiDataAgent:
    """
    多数据源抓取与管理，支持yfinance、finnhub、simfin等。
    """
    def __init__(self, finnhub_key=None):
        # 初始化API密钥和客户端
        self.finnhub_key = finnhub_key
        self.finnhub_client = finnhub.Client(api_key=self.finnhub_key) if self.finnhub_key else None

    def _check_yfinance_ticker(self, tickers: list[str], start_date: str, end_date: str) -> dict[str, pd.DataFrame]:
        """
        批量获取yfinance的公司信息和历史行情。
        """
        print("yfinance".center(50, "="))
        stocks = yf.Tickers(tickers)
        infos = {item: stocks.tickers[item].info for item in tickers}
        print("infos fetched")

        missed = []
        for item in tickers:
            if item not in infos:
                missed.append(item)
        if len(missed) > 0:
            print(f"Ticker {missed} not found in yfinance.")
        else:
            print("All tickers found in yfinance.")

        # 获取历史行情数据
        hist = stocks.history(start=start_date, end=end_date, period=None)
        print("Price history fetched")
        # 调整多重索引格式，便于后续处理
        columns = map(lambda x: (x[1], x[0]), hist.columns)
        hist.columns = pd.MultiIndex.from_tuples(sorted(columns, key=lambda x: x[0]))
        return {'company_info': infos, 'company_history': {item: hist[item] for item in tickers}}

    def _check_finnhub_ticker(self, tickers: list[str], start_date: str, end_date: str, limit: int = 10) -> dict[str, dict]:
        """
        批量获取finnhub的公司信息、新闻、财务等。
        """
        print("finnhub".center(50, "="))
        # 公司基本信息
        profiles = [self.finnhub_client.company_profile2(symbol=item) for item in tickers]
        print("company_profile fetched")
        # 新闻
        company_news = {item: self.finnhub_client.company_news(symbol=item, _from=start_date, to=end_date) for item in tickers}
        print("company_news fetched")
        time.sleep(1.5)
        # 内部人情绪
        insider_sentiment = {item: self.finnhub_client.stock_insider_sentiment(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers}
        print("insider_sentiment fetched")
        time.sleep(1.5)
        # 政府支出
        usa_spending = {item: self.finnhub_client.stock_usa_spending(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers}
        print("usa_spending fetched")
        time.sleep(1.5)
        # 游说活动
        lobbying = {item: self.finnhub_client.stock_lobbying(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers}
        print("lobbying fetched")
        time.sleep(1.5)
        # 签证申请
        visa_application = {item: self.finnhub_client.stock_visa_application(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers}
        print("visa_application fetched")
        time.sleep(1.5)
        # 专利
        uspto_patents = {item: self.finnhub_client.stock_uspto_patent(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers}
        print("uspto_patents fetched")
        time.sleep(1.5)
        # 盈利意外
        earning_suprice = {item: self.finnhub_client.company_earnings(symbol=item, limit=limit) for item in tickers}
        print("earning_suprice fetched")
        # 返回所有抓取结果
        return {'company_profile': profiles, 'company_news': company_news, 'insider_sentiment': insider_sentiment, 'usa_spending': usa_spending, 'lobbying': lobbying, 'visa_application': visa_application, 'uspto_patents': uspto_patents, 'earning_suprice': earning_suprice}

    def _check_simfin_ticker(self, tickers: list[str], start_date: str, end_date: str) -> list[dict]:
        """
        批量获取simfin的公司财报。
        """
        print("simfin".center(50, "="))
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
        print("simfin results fetched")
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


    def _data_extraction_simfin(self,   tickers: list[str], start_date: str, end_date: str) -> dict:
        results = self._check_simfin_ticker(tickers, start_date, end_date)

        # 提取不同的自由现金流和每股收益
        free_cash_flow, earnings_per_share = self._simfin_data_extraction(results)
        
    
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
        print("yfinance results saved.")

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
                    print(f"[finnhub] Error: {key} - {ticker} - {e}")
        print("finnhub results saved.")

    def _fetching_simfin_ticker(self, tickers: list[str], start_date: str, end_date: str, dir: str = "simfin_results"):
        """
        抓取simfin数据并保存本地。
        """
        simfin_results = self._check_simfin_ticker(tickers, start_date, end_date)
        if not os.path.exists(dir):
            os.mkdir(dir)
        with open(f"{dir}/simfin_results.json", "w") as f:
            json.dump(simfin_results, f, indent=2, ensure_ascii=False)
        print("simfin results saved.")

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

if __name__ == "__main__":
    print("=== MultiDataAgent 基本连接和 ticker 检查 ===")
    dotenv.load_dotenv()
    FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', "d1srh21r01qhe5rblou0d1srh21r01qhe5rbloug")

    agent = MultiDataAgent(FINNHUB_API_KEY)
    tickers = ['AAPL', 'MSFT']
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    dir_ = "results"

    agent.fetching_all_ticker(tickers, start_date, end_date, dir_)