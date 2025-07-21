import yfinance as yf

class MarketDataAgent:
    """Agent for retrieving real-time or historical market data (e.g., Yahoo Finance)."""
    def fetch(self, ticker: str, period: str = '1mo', interval: str = '1d'):
        """Fetch historical market data for a given ticker symbol."""
        stock = yf.Ticker(ticker)
        return stock.history(period=period, interval=interval) 