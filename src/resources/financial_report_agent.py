from sec_edgar_downloader import Downloader

class FinancialReportAgent:
    """Agent for fetching and parsing financial reports (e.g., SEC filings)."""
    def __init__(self, download_folder="sec_filings"):
        self.dl = Downloader(download_folder)

    def fetch(self, ticker: str, filing_type: str = "10-K"):
        """Fetch SEC filings (e.g., 10-K, 10-Q) for a given ticker symbol."""
        self.dl.get(filing_type, ticker)
        # Returns the path to the downloaded files
        return f"{self.dl.save_path}/{ticker}/{filing_type}" 