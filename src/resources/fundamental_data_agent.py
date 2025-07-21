import yfinance as yf
import finnhub
import simfin as sf

class FundamentalDataAgent:
    """Agent for retrieving fundamental financial data (e.g., Yahoo Finance, Finnhub, SimFin)."""
    def __init__(self, finnhub_key=None, simfin_api_key=None):
        self.finnhub_client = finnhub.Client(api_key=finnhub_key) if finnhub_key else None
        if simfin_api_key:
            sf.set_api_key(simfin_api_key)
            sf.set_data_dir('simfin_data')

    def fetch_yfinance(self, ticker: str):
        """Fetch fundamental data using yfinance."""
        stock = yf.Ticker(ticker)
        return stock.info

    def fetch_finnhub(self, ticker: str):
        """Fetch fundamental data using Finnhub."""
        if not self.finnhub_client:
            raise ValueError("Finnhub API key not provided.")
        return self.finnhub_client.company_basic_financials(ticker, 'all')

    def fetch_simfin(self, ticker: str, market='us'):
        """Fetch fundamental data using SimFin."""
        # Example: get income statements
        return sf.load_income(variant='annual', market=market, ticker=ticker) 