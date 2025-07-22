import tweepy
import praw
import os
import dotenv

dotenv.load_dotenv()

class SocialMediaAgent:
    """Agent for collecting and analyzing social media data (e.g., X/Twitter, Reddit)."""
    def __init__(self, twitter_keys=None, reddit_keys=None):
        # twitter_keys: dict with consumer_key, consumer_secret, access_token, access_token_secret
        # reddit_keys: dict with client_id, client_secret, user_agent
        if twitter_keys:
            auth = tweepy.OAuth1UserHandler(
                twitter_keys['consumer_key'],
                twitter_keys['consumer_secret'],
                twitter_keys['access_token'],
                twitter_keys['access_token_secret']
            )
            self.twitter_api = tweepy.API(auth)
        else:
            self.twitter_api = None
        if reddit_keys:
            self.reddit = praw.Reddit(
                client_id=reddit_keys['client_id'],
                client_secret=reddit_keys['client_secret'],
                user_agent=reddit_keys['user_agent']
            )
        else:
            self.reddit = praw.Reddit(
                client_id=os.getenv('CLIENT_ID'),
                client_secret=os.getenv('SECRET_KEY'),
                user_agent=os.getenv('REDDIT_USER_AGENT')
            )

    def fetch_tweets(self, query: str, count: int = 10):
        """Fetch tweets from X/Twitter based on a query string."""
        if not self.twitter_api:
            raise ValueError("Twitter API keys not provided.")
        return self.twitter_api.search_tweets(q=query, count=count)

    def fetch_reddit(self, query: str, limit: int = 10):
        """Fetch Reddit posts based on a query string."""
        if not self.reddit:
            raise ValueError("Reddit API keys not provided.")
        return list(self.reddit.subreddit('all').search(query, limit=limit)) 