from GoogleNews import GoogleNews
from newsapi import NewsApiClient

class NewsAgent:
    """Agent for fetching and processing news articles (e.g., Google News, NewsAPI)."""
    def __init__(self, newsapi_key=None):
        self.googlenews = GoogleNews()
        self.newsapi = NewsApiClient(api_key=newsapi_key) if newsapi_key else None

    def fetch_from_google(self, query: str, period: str = '7d'):
        """Fetch news articles from Google News based on a query string and period (e.g., '7d')."""
        self.googlenews.search(query)
        return self.googlenews.results(sort=True)

    def fetch_from_newsapi(self, query: str, language: str = 'en'):
        """Fetch news articles from NewsAPI based on a query string and language."""
        if not self.newsapi:
            raise ValueError("NewsAPI key not provided.")
        return self.newsapi.get_everything(q=query, language=language) 