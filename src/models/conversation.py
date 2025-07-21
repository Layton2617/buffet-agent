from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    agent_response = db.Column(db.Text, nullable=False)
    reasoning_chain = db.Column(db.Text)
    tool_calls = db.Column(db.Text)
    confidence_score = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_message': self.user_message,
            'agent_response': self.agent_response,
            'reasoning_chain': json.loads(self.reasoning_chain) if self.reasoning_chain else [],
            'tool_calls': json.loads(self.tool_calls) if self.tool_calls else [],
            'confidence_score': self.confidence_score,
            'timestamp': self.timestamp.isoformat()
        }

class BeliefState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    belief_key = db.Column(db.String(100), nullable=False)
    belief_value = db.Column(db.String(200), nullable=False)
    confidence = db.Column(db.Float, default=0.5)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    decay_factor = db.Column(db.Float, default=0.95)
    
    def to_dict(self):
        return {
            'belief_key': self.belief_key,
            'belief_value': self.belief_value,
            'confidence': self.confidence,
            'last_updated': self.last_updated.isoformat(),
            'decay_factor': self.decay_factor
        }

class PortfolioRecommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    company_name = db.Column(db.String(200))
    recommendation = db.Column(db.String(20))
    target_price = db.Column(db.Float)
    current_price = db.Column(db.Float)
    margin_of_safety = db.Column(db.Float)
    dcf_value = db.Column(db.Float)
    pe_ratio = db.Column(db.Float)
    reasoning = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'company_name': self.company_name,
            'recommendation': self.recommendation,
            'target_price': self.target_price,
            'current_price': self.current_price,
            'margin_of_safety': self.margin_of_safety,
            'dcf_value': self.dcf_value,
            'pe_ratio': self.pe_ratio,
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat()
        }

