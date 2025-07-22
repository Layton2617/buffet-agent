import yfinance as yf
import finnhub
import os
import dotenv
import pandas as pd
import requests
import time


# 加载环境变量，便于本地开发和部署
dotenv.load_dotenv()

FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
SIMFIN_API_KEY = os.getenv('SIMFIN_API_KEY')

class FundamentalDataAgent:
    """
    Agent for connecting to yfinance, finnhub, and simfin data sources.
    只做基础连接和 ticker 状态检查，不做全面数据抓取。
    """
    def __init__(self, finnhub_key=None, simfin_api_key=None):
        # yfinance 无需 API key
        self.finnhub_key = finnhub_key or FINNHUB_API_KEY
        self.simfin_api_key = simfin_api_key or SIMFIN_API_KEY
        # 初始化 finnhub 客户端
        self.finnhub_client = finnhub.Client(api_key=self.finnhub_key) if self.finnhub_key else None

    def check_yfinance_ticker(self, tickers: list[str], start_date: str, end_date: str) -> dict[dict, pd.DataFrame]:
        """检查 yfinance ticker 是否存在及其基本信息。"""
        stocks = yf.Tickers(tickers)
        infos = {item: stocks.tickers[item].info for item in tickers}

        missed = []
        for item in tickers:
            if item not in infos:
                missed.append(item)

        if len(missed) > 0:
            print(f"Ticker {missed} not found in yfinance.")
        else:
            print("All tickers found in yfinance.")

        if start_date and end_date:
            hist = stocks.history(start=start_date, end=end_date, period=None)
            print("stocks companies and history data fetched.")
            return {'company_info': infos, 'company_history': hist}
        else:
            print("stocks companies data fetched.")
            return {'company_info': infos, 'company_history': None}

    def check_finnhub_ticker(self, tickers: list[str], start_date: str, end_date: str, limit: int = 10) -> dict[dict, dict]:
        """
        return all data from finnhub
        these data are free to use
        """
        if not self.finnhub_client:
            raise ValueError("Finnhub API key not provided.")
        profiles = {item: self.finnhub_client.company_profile2(symbol=item) for item in tickers}
        if start_date and end_date:
            company_news = {item: self.finnhub_client.company_news(symbol=item, _from=start_date, to=end_date) for item in tickers} # dict[list[dict]], dict[Ticker]
            time.sleep(1)
            insider_sentiment = {item: self.finnhub_client.stock_insider_sentiment(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers} # dict[list[dict]], dict[Ticker]
            time.sleep(1)
            usa_spending = {item: self.finnhub_client.stock_usa_spending(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers} # dict[list[dict]], dict[Ticker]
            time.sleep(1)
            lobbying = {item: self.finnhub_client.stock_lobbying(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers} # dict[list[dict]], dict[Ticker]
            time.sleep(1)
            visa_application = {item: self.finnhub_client.stock_visa_application(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers} # dict[list[dict]], dict[Ticker]
            time.sleep(1)
            uspto_patents = {item: self.finnhub_client.stock_uspto_patent(symbol=item, _from=start_date, to=end_date).get('data') for item in tickers} # dict[list[dict]], dict[Ticker]
            time.sleep(1)
            earning_suprice = {item: self.finnhub_client.company_earnings(symbol=item, limit=limit) for item in tickers} # dict[list[dict]], dict[Ticker]
            time.sleep(1)
            basic_financials = {item: self.finnhub_client.company_basic_financials(symbol=item, metric='all') for item in tickers}
            return {'company_profile': profiles, 'company_news': company_news, 'insider_sentiment': insider_sentiment, 'usa_spending': usa_spending, 'lobbying': lobbying, 'visa_application': visa_application, 'uspto_patents': uspto_patents, 'earning_suprice': earning_suprice, 'basic_financials': basic_financials}
        else:
            return {'company_profile': profiles, 'company_news': None, 'insider_sentiment': None, 'usa_spending': None, 'lobbying': None, 'visa_application': None, 'uspto_patents': None, 'earning_suprice': None, 'basic_financials': None}

    def check_simfin_ticker(self, tickers: list[str], start_date: str, end_date: str) -> list[dict]: # list[0] = Ticker's Dict including all statements
        """检查 simfin ticker 是否有效（返回公司基本信息）。"""
        if not start_date and not end_date:
            raise ValueError("Start and end date are required.")

        urls = [
            "https://backend.simfin.com/api/v3/companies/statements/compact?ticker={tickers}&statements=PL,BS,CF,DERIVED&start={start}&end={end}&details=false"
                ]

        headers = {
            "accept": "application/json",
            "Authorization": os.getenv('AUTHORIZATION')
        }
        results = []
        for item in urls:
            item = item.format(tickers=",".join(tickers), start=start_date, end=end_date)
            response = requests.get(item, headers=headers)
            assert response.status_code == 200, f"Failed to fetch data from SimFin.\n{response.status_code}\n{response.text}\n{item}"
            results = response.json()
            results.append(results)
        return results

if __name__ == "__main__":
    print("=== FundamentalDataAgent 基本连接和 ticker 检查 ===")
    agent = FundamentalDataAgent()
    tickers = ['AAPL', 'MSFT']
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    # print("Testing yfinance...")
    # yf_results = agent.check_yfinance_ticker(tickers, start_date, end_date)
    # print(yf_results.get('company_info').get('AAPL'))
    # print(yf_results.get('company_history').sample())
    # print("Testing finnhub...")
    # finnhub_results = agent.check_finnhub_ticker(tickers, start_date, end_date)
    # print(finnhub_results.get('company_profile').get('AAPL'))
    # print(finnhub_results.get('company_news').get('AAPL')[0])
    # print(finnhub_results.get('insider_sentiment').get('AAPL')[0])
    # print(finnhub_results.get('usa_spending').get('AAPL')[0])
    # print(finnhub_results.get('lobbying').get('AAPL')[0])
    print("Testing simfin...")
    simfin_results = agent.check_simfin_ticker(tickers, start_date, end_date)
    print(simfin_results[0])