import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math

class BeliefTracker:
    def __init__(self):
        self.beliefs = {}
        self.belief_history = []
        self.causal_links = {}
        
    def update_belief(self, key: str, value: str, confidence: float = 0.7, 
                     decay_factor: float = 0.95) -> None:
        
        timestamp = datetime.utcnow()
        
        old_belief = self.beliefs.get(key)
        if old_belief:
            self.belief_history.append({
                'key': key,
                'old_value': old_belief['value'],
                'new_value': value,
                'old_confidence': old_belief['confidence'],
                'new_confidence': confidence,
                'timestamp': timestamp.isoformat(),
                'change_type': 'update'
            })
        else:
            self.belief_history.append({
                'key': key,
                'old_value': None,
                'new_value': value,
                'old_confidence': 0.0,
                'new_confidence': confidence,
                'timestamp': timestamp.isoformat(),
                'change_type': 'new'
            })
        
        self.beliefs[key] = {
            'value': value,
            'confidence': confidence,
            'last_updated': timestamp,
            'decay_factor': decay_factor,
            'update_count': self.beliefs.get(key, {}).get('update_count', 0) + 1
        }
    
    def get_belief(self, key: str) -> Optional[Dict]:
        
        if key not in self.beliefs:
            return None
        
        belief = self.beliefs[key].copy()
        
        time_diff = datetime.utcnow() - belief['last_updated']
        hours_passed = time_diff.total_seconds() / 3600
        
        decayed_confidence = belief['confidence'] * (belief['decay_factor'] ** (hours_passed / 24))
        belief['current_confidence'] = max(0.1, decayed_confidence)
        
        return belief
    
    def get_all_beliefs(self) -> Dict:
        
        current_beliefs = {}
        for key in self.beliefs:
            belief = self.get_belief(key)
            if belief and belief['current_confidence'] > 0.2:
                current_beliefs[key] = belief
        
        return current_beliefs
    
    def add_causal_link(self, cause: str, effect: str, strength: float = 0.5) -> None:
        
        if cause not in self.causal_links:
            self.causal_links[cause] = []
        
        self.causal_links[cause].append({
            'effect': effect,
            'strength': strength,
            'created': datetime.utcnow().isoformat()
        })
    
    def get_influenced_beliefs(self, belief_key: str) -> List[Dict]:
        
        influenced = []
        if belief_key in self.causal_links:
            for link in self.causal_links[belief_key]:
                effect_belief = self.get_belief(link['effect'])
                if effect_belief:
                    influenced.append({
                        'belief': effect_belief,
                        'influence_strength': link['strength']
                    })
        
        return influenced
    
    def get_belief_summary(self) -> Dict:
        
        beliefs = self.get_all_beliefs()
        
        high_confidence = {k: v for k, v in beliefs.items() 
                          if v['current_confidence'] > 0.7}
        medium_confidence = {k: v for k, v in beliefs.items() 
                           if 0.4 <= v['current_confidence'] <= 0.7}
        low_confidence = {k: v for k, v in beliefs.items() 
                         if v['current_confidence'] < 0.4}
        
        return {
            'total_beliefs': len(beliefs),
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence,
            'low_confidence': low_confidence,
            'causal_links_count': len(self.causal_links),
            'recent_changes': self.belief_history[-5:] if self.belief_history else []
        }
    
    def initialize_default_beliefs(self) -> None:
        
        default_beliefs = [
            ('fed_policy', 'neutral', 0.6),
            ('inflation_trend', 'moderate', 0.5),
            ('market_sentiment', 'cautious', 0.7),
            ('economic_growth', 'steady', 0.6),
            ('interest_rates', 'stable', 0.8),
            ('consumer_confidence', 'moderate', 0.5),
            ('corporate_earnings', 'growing', 0.6),
            ('geopolitical_risk', 'elevated', 0.7),
            ('technology_disruption', 'accelerating', 0.8),
            ('energy_transition', 'ongoing', 0.9)
        ]
        
        for key, value, confidence in default_beliefs:
            self.update_belief(key, value, confidence)
        
        causal_relationships = [
            ('fed_policy', 'interest_rates', 0.9),
            ('interest_rates', 'market_sentiment', 0.7),
            ('inflation_trend', 'fed_policy', 0.8),
            ('economic_growth', 'corporate_earnings', 0.8),
            ('geopolitical_risk', 'market_sentiment', 0.6),
            ('consumer_confidence', 'economic_growth', 0.7)
        ]
        
        for cause, effect, strength in causal_relationships:
            self.add_causal_link(cause, effect, strength)
    
    def update_beliefs_from_news(self, news_summary: str) -> List[str]:
        
        updates = []
        news_lower = news_summary.lower()
        
        if any(word in news_lower for word in ['rate hike', 'interest rate increase', 'fed raises']):
            self.update_belief('fed_policy', 'tightening', 0.8)
            updates.append('Updated Fed policy to tightening')
        
        if any(word in news_lower for word in ['rate cut', 'interest rate decrease', 'fed lowers']):
            self.update_belief('fed_policy', 'easing', 0.8)
            updates.append('Updated Fed policy to easing')
        
        if any(word in news_lower for word in ['inflation rising', 'price increases', 'cpi up']):
            self.update_belief('inflation_trend', 'rising', 0.7)
            updates.append('Updated inflation trend to rising')
        
        if any(word in news_lower for word in ['market crash', 'sell-off', 'panic']):
            self.update_belief('market_sentiment', 'fearful', 0.9)
            updates.append('Updated market sentiment to fearful')
        
        if any(word in news_lower for word in ['market rally', 'bull market', 'optimism']):
            self.update_belief('market_sentiment', 'greedy', 0.8)
            updates.append('Updated market sentiment to greedy')
        
        return updates

