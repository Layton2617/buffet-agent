import json
import numpy as np
from typing import List, Dict, Tuple
import re

class BuffettRAG:
    """
    RAG（检索增强生成）系统，管理语料库和检索。
    """
    def __init__(self):
        # 加载语料库
        self.corpus = self._load_buffett_corpus()
        self.embeddings = {}
        
    def _load_buffett_corpus(self) -> List[Dict]:
        """
        加载巴菲特语录/信件等文本。
        """
        
        return [
            {
                "id": "1977_01",
                "year": 1977,
                "text": "The primary test of managerial economic performance is the achievement of a high earnings rate on equity capital employed (without undue leverage, accounting gimmickry, etc.) and not the achievement of consistent gains in earnings per share.",
                "topic": "management_performance"
            },
            {
                "id": "1988_01", 
                "year": 1988,
                "text": "Time is the friend of the wonderful business, the enemy of the mediocre. You might think this principle is obvious, but I had to learn it the hard way - by buying Berkshire Hathaway.",
                "topic": "business_quality"
            },
            {
                "id": "1989_01",
                "year": 1989,
                "text": "It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price.",
                "topic": "valuation_philosophy"
            },
            {
                "id": "1992_01",
                "year": 1992,
                "text": "Risk comes from not knowing what you're doing. The stock market is a voting machine in the short run, but a weighing machine in the long run.",
                "topic": "risk_management"
            },
            {
                "id": "1996_01",
                "year": 1996,
                "text": "Most investors, both institutional and individual, will find that the best way to own common stocks is through an index fund that charges minimal fees.",
                "topic": "investment_advice"
            },
            {
                "id": "2001_01",
                "year": 2001,
                "text": "In the business world, the rearview mirror is always clearer than the windshield. Predicting rain doesn't count; building arks does.",
                "topic": "market_prediction"
            },
            {
                "id": "2008_01",
                "year": 2008,
                "text": "Be fearful when others are greedy and greedy when others are fearful. A simple rule dictates my buying: Be fearful when others are greedy and greedy when others are fearful.",
                "topic": "market_sentiment"
            },
            {
                "id": "2013_01",
                "year": 2013,
                "text": "The stock market is designed to transfer money from the Active to the Patient. Our favorite holding period is forever.",
                "topic": "long_term_investing"
            },
            {
                "id": "2016_01",
                "year": 2016,
                "text": "Price is what you pay. Value is what you get. Whether we're talking about socks or stocks, I like buying quality merchandise when it's marked down.",
                "topic": "value_investing"
            },
            {
                "id": "2020_01",
                "year": 2020,
                "text": "Never bet against America. In the 20th century, the United States endured two world wars and other traumatic and expensive military conflicts; the Depression; a dozen or so recessions and financial panics; oil shocks; a flu epidemic; and the resignation of a disgraced president. Yet the Dow rose from 66 to 11,497.",
                "topic": "american_optimism"
            }
        ]
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """
        将文本转为简单向量，用于相似度计算。
        """
        
        words = re.findall(r'\w+', text.lower())
        vocab = ['buy', 'sell', 'value', 'price', 'market', 'stock', 'company', 'business', 
                'investment', 'risk', 'return', 'growth', 'earnings', 'profit', 'management',
                'quality', 'time', 'patient', 'fearful', 'greedy', 'wonderful', 'fair']
        
        embedding = np.zeros(len(vocab))
        for i, word in enumerate(vocab):
            embedding[i] = words.count(word)
        
        norm = np.linalg.norm(embedding)
        return embedding / norm if norm > 0 else embedding
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        根据查询语句检索最相关的语料。
        """
        
        query_embedding = self._simple_embedding(query)
        
        scores = []
        for doc in self.corpus:
            doc_embedding = self._simple_embedding(doc['text'])
            similarity = np.dot(query_embedding, doc_embedding)
            scores.append((similarity, doc))
        
        scores.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for score, doc in scores[:top_k]:
            results.append({
                'score': float(score),
                'document': doc,
                'relevance': 'high' if score > 0.3 else 'medium' if score > 0.1 else 'low'
            })
        
        return results
    
    def get_context_for_query(self, query: str) -> str:
        """
        为用户问题生成上下文片段。
        """
        
        results = self.search(query, top_k=3)
        
        context_parts = []
        for result in results:
            doc = result['document']
            context_parts.append(f"From {doc['year']} letter: {doc['text']}")
        
        return "\n\n".join(context_parts)
    
    def get_topic_documents(self, topic: str) -> List[Dict]:
        """
        按主题检索语料。
        """
        
        return [doc for doc in self.corpus if doc.get('topic') == topic]
    
    def get_historical_context(self, year_range: Tuple[int, int]) -> List[Dict]:
        """
        按年份区间检索语料。
        """
        
        start_year, end_year = year_range
        return [doc for doc in self.corpus 
                if start_year <= doc['year'] <= end_year]

