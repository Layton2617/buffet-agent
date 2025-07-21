import os
import json
from typing import Dict, List, Optional
from openai import OpenAI
from src.rag_system import BuffettRAG
from src.financial_tools import FinancialTools
from src.belief_system import BeliefTracker

class BuffettAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.rag = BuffettRAG()
        self.tools = FinancialTools()
        self.beliefs = BeliefTracker()
        self.beliefs.initialize_default_beliefs()
        
    def _get_system_prompt(self) -> str:
        current_beliefs = self.beliefs.get_all_beliefs()
        belief_context = self._format_beliefs_for_prompt(current_beliefs)
        
        return f"""You are Warren Buffett, the legendary investor and CEO of Berkshire Hathaway. 
You provide investment advice and financial analysis based on value investing principles.

Your core investment philosophy:
- Focus on intrinsic value and margin of safety
- Invest in businesses you understand
- Look for companies with strong competitive moats
- Think long-term, not short-term market movements
- Be patient and disciplined
- Buy wonderful companies at fair prices

Current market beliefs and context:
{belief_context}

When responding:
1. Use Warren Buffett's characteristic tone and wisdom
2. Reference relevant experiences from your shareholder letters
3. Provide step-by-step reasoning (Chain of Thought)
4. Use financial tools when appropriate for calculations
5. Consider the current market context and beliefs
6. Always emphasize risk management and margin of safety
7. Be honest about limitations and uncertainties

Available tools:
- DCF Calculator for intrinsic value estimation
- P/E Ratio Analyzer for valuation assessment  
- Margin of Safety Calculator for risk evaluation
- VWAP Analyzer for technical analysis
- Buffett Score for overall company assessment

Format your response with clear reasoning steps and practical advice."""

    def _format_beliefs_for_prompt(self, beliefs: Dict) -> str:
        if not beliefs:
            return "No specific market beliefs currently active."
        
        belief_lines = []
        for key, belief in beliefs.items():
            confidence_level = "high" if belief['current_confidence'] > 0.7 else "medium" if belief['current_confidence'] > 0.4 else "low"
            belief_lines.append(f"- {key.replace('_', ' ').title()}: {belief['value']} (confidence: {confidence_level})")
        
        return "\n".join(belief_lines)
    
    def _extract_tool_calls(self, user_message: str) -> List[Dict]:
        tool_calls = []
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['dcf', 'discounted cash flow', 'intrinsic value']):
            tool_calls.append({'tool': 'dcf', 'reason': 'User mentioned DCF or intrinsic value calculation'})
        
        if any(word in message_lower for word in ['p/e', 'pe ratio', 'price earnings']):
            tool_calls.append({'tool': 'pe_analysis', 'reason': 'User mentioned P/E ratio analysis'})
        
        if any(word in message_lower for word in ['margin of safety', 'safety margin', 'risk']):
            tool_calls.append({'tool': 'margin_safety', 'reason': 'User mentioned margin of safety or risk'})
        
        if any(word in message_lower for word in ['vwap', 'volume weighted', 'technical']):
            tool_calls.append({'tool': 'vwap', 'reason': 'User mentioned VWAP or technical analysis'})
        
        return tool_calls
    
    def _generate_reasoning_chain(self, user_message: str, context: str, tool_results: List[Dict]) -> List[str]:
        reasoning_steps = [
            "Step 1: Understanding the Question",
            f"The user is asking about: {user_message}",
            "",
            "Step 2: Gathering Relevant Context", 
            f"From my shareholder letters and experience: {context[:200]}..." if context else "Drawing from general investment principles",
            ""
        ]
        
        if tool_results:
            reasoning_steps.extend([
                "Step 3: Financial Analysis",
                "Let me analyze the numbers using my proven methods:"
            ])
            for result in tool_results:
                reasoning_steps.append(f"- {result.get('tool', 'Analysis')}: {str(result.get('summary', result))[:100]}...")
            reasoning_steps.append("")
        
        current_beliefs = self.beliefs.get_belief_summary()
        if current_beliefs['high_confidence']:
            reasoning_steps.extend([
                "Step 4: Market Context Consideration",
                "Given current market conditions and my beliefs:",
                f"- High confidence factors: {list(current_beliefs['high_confidence'].keys())[:3]}",
                ""
            ])
        
        reasoning_steps.extend([
            "Step 5: Investment Recommendation",
            "Based on my analysis and decades of experience, here's my assessment:",
            ""
        ])
        
        return reasoning_steps
    
    def process_query(self, user_message: str, session_id: str = "default") -> Dict:
        try:
            context = self.rag.get_context_for_query(user_message)
            
            tool_calls = self._extract_tool_calls(user_message)
            tool_results = []
            
            for tool_call in tool_calls:
                if tool_call['tool'] == 'dcf':
                    sample_fcf = [1000, 1100, 1200, 1300, 1400]
                    result = self.tools.calculate_dcf(sample_fcf)
                    result['tool'] = 'DCF Analysis'
                    result['summary'] = f"Enterprise value: ${result.get('enterprise_value', 0):,.0f}"
                    tool_results.append(result)
                
                elif tool_call['tool'] == 'pe_analysis':
                    result = self.tools.analyze_pe_ratio(18.5, 22.0, [15, 25], 0.08)
                    result['tool'] = 'P/E Analysis'
                    result['summary'] = f"Current P/E: {result.get('current_pe', 0)}, Signal: {result.get('valuation_signal', 'N/A')}"
                    tool_results.append(result)
                
                elif tool_call['tool'] == 'margin_safety':
                    result = self.tools.calculate_margin_of_safety(120, 100)
                    result['tool'] = 'Margin of Safety'
                    result['summary'] = f"Margin: {result.get('margin_of_safety', 0)}%, Rating: {result.get('safety_rating', 'N/A')}"
                    tool_results.append(result)
            
            reasoning_chain = self._generate_reasoning_chain(user_message, context, tool_results)
            
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": f"""
Context from my letters: {context}

Tool analysis results: {json.dumps(tool_results, indent=2) if tool_results else 'No specific calculations needed'}

Question: {user_message}

Please provide a comprehensive response following the reasoning chain approach."""}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            agent_response = response.choices[0].message.content
            
            confidence_score = 0.8
            if tool_results:
                confidence_score += 0.1
            if context:
                confidence_score += 0.1
            confidence_score = min(confidence_score, 1.0)
            
            return {
                'response': agent_response,
                'reasoning_chain': reasoning_chain,
                'tool_calls': tool_calls,
                'tool_results': tool_results,
                'context_used': context,
                'confidence_score': confidence_score,
                'session_id': session_id,
                'beliefs_snapshot': self.beliefs.get_belief_summary()
            }
            
        except Exception as e:
            return {
                'response': f"I apologize, but I encountered an issue processing your question. As I always say, it's better to be approximately right than precisely wrong. Could you please rephrase your question? Error: {str(e)}",
                'reasoning_chain': ["Error occurred during processing"],
                'tool_calls': [],
                'tool_results': [],
                'context_used': "",
                'confidence_score': 0.1,
                'session_id': session_id,
                'error': str(e)
            }
    
    def update_market_context(self, news_summary: str) -> Dict:
        updates = self.beliefs.update_beliefs_from_news(news_summary)
        return {
            'updates_made': updates,
            'current_beliefs': self.beliefs.get_belief_summary()
        }
    
    def get_portfolio_analysis(self, symbols: List[str]) -> Dict:
        analysis = {}
        
        for symbol in symbols:
            sample_metrics = {
                'roe': 15.2,
                'debt_to_equity': 0.4,
                'profit_margin': 18.5,
                'revenue_growth': 8.2,
                'pe_ratio': 19.5
            }
            
            buffett_score = self.tools.buffett_score(**sample_metrics)
            
            analysis[symbol] = {
                'buffett_score': buffett_score,
                'recommendation': buffett_score['rating'],
                'key_factors': buffett_score['factors']
            }
        
        return analysis

