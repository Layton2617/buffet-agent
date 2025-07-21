from flask import Blueprint, request, jsonify
from src.buffett_agent import BuffettAgent
from src.models.conversation import db, Conversation, BeliefState, PortfolioRecommendation
import json
import uuid
from datetime import datetime

buffett_bp = Blueprint('buffett', __name__)

agent = BuffettAgent()

@buffett_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        result = agent.process_query(user_message, session_id)
        
        conversation = Conversation(
            session_id=session_id,
            user_message=user_message,
            agent_response=result['response'],
            reasoning_chain=json.dumps(result['reasoning_chain']),
            tool_calls=json.dumps(result['tool_calls']),
            confidence_score=result['confidence_score']
        )
        
        db.session.add(conversation)
        db.session.commit()
        
        return jsonify({
            'response': result['response'],
            'reasoning_chain': result['reasoning_chain'],
            'tool_results': result['tool_results'],
            'confidence_score': result['confidence_score'],
            'session_id': session_id,
            'conversation_id': conversation.id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buffett_bp.route('/conversation/<session_id>', methods=['GET'])
def get_conversation(session_id):
    try:
        conversations = Conversation.query.filter_by(session_id=session_id).order_by(Conversation.timestamp).all()
        return jsonify([conv.to_dict() for conv in conversations])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buffett_bp.route('/tools/dcf', methods=['POST'])
def calculate_dcf():
    try:
        data = request.get_json()
        free_cash_flows = data.get('free_cash_flows', [])
        terminal_growth_rate = data.get('terminal_growth_rate', 0.025)
        discount_rate = data.get('discount_rate', 0.10)
        
        result = agent.tools.calculate_dcf(free_cash_flows, terminal_growth_rate, discount_rate)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buffett_bp.route('/tools/pe', methods=['POST'])
def analyze_pe():
    try:
        data = request.get_json()
        current_pe = data.get('current_pe')
        industry_avg_pe = data.get('industry_avg_pe')
        historical_pe_range = data.get('historical_pe_range', [])
        earnings_growth_rate = data.get('earnings_growth_rate', 0)
        
        result = agent.tools.analyze_pe_ratio(current_pe, industry_avg_pe, historical_pe_range, earnings_growth_rate)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buffett_bp.route('/tools/margin', methods=['POST'])
def calculate_margin():
    try:
        data = request.get_json()
        intrinsic_value = data.get('intrinsic_value')
        current_price = data.get('current_price')
        minimum_margin = data.get('minimum_margin', 0.20)
        
        result = agent.tools.calculate_margin_of_safety(intrinsic_value, current_price, minimum_margin)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buffett_bp.route('/tools/buffett-score', methods=['POST'])
def buffett_score():
    try:
        data = request.get_json()
        roe = data.get('roe')
        debt_to_equity = data.get('debt_to_equity')
        profit_margin = data.get('profit_margin')
        revenue_growth = data.get('revenue_growth')
        pe_ratio = data.get('pe_ratio')
        
        result = agent.tools.buffett_score(roe, debt_to_equity, profit_margin, revenue_growth, pe_ratio)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buffett_bp.route('/beliefs', methods=['GET'])
def get_beliefs():
    try:
        beliefs = agent.beliefs.get_belief_summary()
        return jsonify(beliefs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buffett_bp.route('/beliefs/update', methods=['POST'])
def update_beliefs():
    try:
        data = request.get_json()
        news_summary = data.get('news_summary', '')
        
        result = agent.update_market_context(news_summary)
        
        for key, belief_data in result['current_beliefs']['high_confidence'].items():
            existing_belief = BeliefState.query.filter_by(belief_key=key).first()
            if existing_belief:
                existing_belief.belief_value = belief_data['value']
                existing_belief.confidence = belief_data['current_confidence']
                existing_belief.last_updated = datetime.utcnow()
            else:
                new_belief = BeliefState(
                    belief_key=key,
                    belief_value=belief_data['value'],
                    confidence=belief_data['current_confidence']
                )
                db.session.add(new_belief)
        
        db.session.commit()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buffett_bp.route('/portfolio/analyze', methods=['POST'])
def analyze_portfolio():
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        analysis = agent.get_portfolio_analysis(symbols)
        
        for symbol, analysis_data in analysis.items():
            recommendation = PortfolioRecommendation(
                symbol=symbol,
                company_name=f"{symbol} Company",
                recommendation=analysis_data['recommendation'],
                reasoning=json.dumps(analysis_data['key_factors'])
            )
            db.session.add(recommendation)
        
        db.session.commit()
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buffett_bp.route('/corpus/search', methods=['POST'])
def search_corpus():
    try:
        data = request.get_json()
        query = data.get('query', '')
        top_k = data.get('top_k', 3)
        
        results = agent.rag.search(query, top_k)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buffett_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'agent': 'Warren Buffett AI',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

