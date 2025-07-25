import os
import json
from typing import Dict, List, Optional
from openai import OpenAI
from src.rag_system import BuffettRAG
from src.financial_tools import FinancialTools
from src.belief_system import BeliefTracker
from src.resources.fin_data import MultiDataAgent
from datetime import datetime, timedelta
from src.parse_tools import LangChainTools
import sys
from tqdm import tqdm


class BuffettAgent:
    """
    巴菲特智能体核心类，负责整合RAG、金融工具、信念系统，处理用户请求。
    """

    def __init__(self):
        # 初始化OpenAI、RAG、金融工具、信念系统
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.rag = BuffettRAG()
        self.tools = FinancialTools()
        self.beliefs = BeliefTracker()
        self.beliefs.initialize_default_beliefs()
        self.fin_data = MultiDataAgent(finnhub_key=os.getenv("FINNHUB_API_KEY"))

    def _get_system_prompt(self) -> str:
        """
        生成系统提示词，包含当前信念和投资原则。
        """
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
        """
        将信念字典格式化为字符串，便于嵌入提示词。
        """
        if not beliefs:
            return "No specific market beliefs currently active."

        belief_lines = []
        for key, belief in beliefs.items():
            confidence_level = (
                "high"
                if belief["current_confidence"] > 0.7
                else "medium" if belief["current_confidence"] > 0.4 else "low"
            )
            belief_lines.append(
                f"- {key.replace('_', ' ').title()}: {belief['value']} (confidence: {confidence_level})"
            )

        return "\n".join(belief_lines)

    def _extract_tool_calls(self, user_message: str) -> List[Dict]:
        """
        根据用户消息内容，自动判断需要调用哪些金融工具。
        """
        tool_calls = []
        message_lower = user_message.lower()

        if any(
            word in message_lower
            for word in ["dcf", "discounted cash flow", "intrinsic value"]
        ):
            tool_calls.append(
                {
                    "tool": "dcf",
                    "reason": "User mentioned DCF or intrinsic value calculation",
                }
            )

        if any(word in message_lower for word in ["p/e", "pe ratio", "price earnings", "pe"]):
            tool_calls.append(
                {"tool": "pe_analysis", "reason": "User mentioned P/E ratio analysis"}
            )

        if any(
            word in message_lower
            for word in ["margin of safety", "safety margin", "risk"]
        ):
            tool_calls.append(
                {
                    "tool": "margin_safety",
                    "reason": "User mentioned margin of safety or risk",
                }
            )

        if any(
            word in message_lower for word in ["vwap", "volume weighted", "technical"]
        ):
            tool_calls.append(
                {"tool": "vwap", "reason": "User mentioned VWAP or technical analysis"}
            )

        return tool_calls

    def _generate_reasoning_chain(
        self, user_message: str, context: str, tool_results: List[Dict]
    ) -> List[str]:
        """
        生成分步推理链，解释智能体的分析过程。
        """
        reasoning_steps = [
            "Step 1: Understanding the Question",
            f"The user is asking about: {user_message}",
            "",
            "Step 2: Gathering Relevant Context",
            (
                f"From my shareholder letters and experience: {context[:200]}..."
                if context
                else "Drawing from general investment principles"
            ),
            "",
        ]

        if tool_results:
            reasoning_steps.extend(
                [
                    "Step 3: Financial Analysis",
                    "Let me analyze the numbers using my proven methods, number is in US dollars or decimals for growth rate or discount rate:",
                ]
            )
            for result in tool_results:
                reasoning_steps.append(
                    f"- {result.get('tool', 'Analysis')}: {str(result.get('summary', result))[:100]}..."
                )
                # 新增：详细展示每个ticker的数据
                data = result.get("data", {})
                if isinstance(data, dict):
                    for ticker, analysis in data.items():
                        reasoning_steps.append(f"  {ticker}:")
                        if isinstance(analysis, dict):
                            for k, v in analysis.items():
                                reasoning_steps.append(f"{k}: {v}")
                        else:
                            reasoning_steps.append(f"    {analysis}")
                else:
                    reasoning_steps.append(f"  {data}")
            reasoning_steps.append("")

        current_beliefs = self.beliefs.get_belief_summary()
        if current_beliefs["high_confidence"]:
            reasoning_steps.extend(
                [
                    "Step 4: Market Context Consideration",
                    "Given current market conditions and my beliefs:",
                    f"- High confidence factors: {list(current_beliefs['high_confidence'].keys())[:10]}",
                    "",
                ]
            )

        reasoning_steps.extend(
            [
                "Step 5: Investment Recommendation",
                "Based on my analysis and decades of experience, here's my assessment:",
                "",
            ]
        )

        return reasoning_steps

    def process_query(self, user_message: str, session_id: str = "default") -> Dict:
        print(f"[process_query] 用户消息: {user_message}", file=sys.stderr)
        try:
            context = self.rag.get_context_for_query(user_message)
            print(f"[process_query] RAG context: {context}", file=sys.stderr)
            print("-"*50, file=sys.stderr)
            tickers = LangChainTools.filter_valid_tickers(user_message)
            print(f"[process_query] 解析出的tickers: {tickers}", file=sys.stderr)
            print("-"*50, file=sys.stderr)
            if tickers:
                self.get_news_about_symbols(tickers)
            tool_calls = self._extract_tool_calls(user_message)
            print(f"[process_query] tool_calls: {tool_calls}", file=sys.stderr)
            print("-"*50, file=sys.stderr)
            tool_results = []
            for tool_call in tool_calls:
                if tool_call["tool"] == "dcf":
                    tickers_fcf = self.fin_data.get_tickers_fcf(tickers)
                    result = {"data": {}}
                    for ticker, fcf in tickers_fcf.items():
                        result["data"][ticker] = self.tools.simple_gordon_dcf(fcf)
                    result["tool"] = "DCF Analysis"
                    result["summary"] = (
                        f"DCF value: ${result.get('DCF', 0):,.2f}"
                    )
                    tool_results.append(result)

                elif tool_call["tool"] == "pe_analysis":
                    pe_inputs = self.fin_data.get_pe_analysis_inputs_for_tickers(
                        tickers, 10
                    )
                    result = {"data": {}}
                    for ticker, inputs in pe_inputs.items():
                        result["data"][ticker] = self.tools.analyze_pe_ratio(**inputs)
                    result["tool"] = "P/E Analysis"
                    result["summary"] = (
                        f"Current P/E: {result.get('current_pe', 0)}, Signal: {result.get('valuation_signal', 'N/A')}"
                    )
                    tool_results.append(result)

                elif tool_call["tool"] == "margin_safety":
                    tickers_margin_safety = self.fin_data.get_tickers_margin_safety(
                        tickers
                    )
                    result = {"data": {}}
                    for ticker, inputs in tickers_margin_safety.items():
                        if "error" in inputs:
                            result["data"][ticker] = {"error": inputs["error"]}
                        else:
                            result["data"][ticker] = (
                                self.tools.calculate_margin_of_safety(**inputs)
                            )
                    result["tool"] = "Margin of Safety"
                    result["summary"] = (
                        f"Margin: {result.get('margin_of_safety', 0)}%, Rating: {result.get('safety_rating', 'N/A')}"
                    )
                    tool_results.append(result)
                    
            with open("tool_results.json", "w") as f:
                json.dump(tool_results, f, indent=2)
            reasoning_chain = self._generate_reasoning_chain(
                user_message, context, tool_results
            )
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {
                    "role": "user",
                    "content": f"""
Context from my letters: {context}

Tool analysis results: {json.dumps(tool_results, indent=2) if tool_results else 'No specific calculations needed'}

Question: {user_message}

Please provide a comprehensive response following the reasoning chain approach.""",
                },
            ]
            response = self.client.chat.completions.create(
                model="gpt-4", messages=messages, temperature=0.7, max_tokens=1500
            )
            agent_response = response.choices[0].message.content
            confidence_score = 0.8
            if tool_results:
                confidence_score += 0.1
            if context:
                confidence_score += 0.1
            confidence_score = min(confidence_score, 1.0)
            return {
                "response": agent_response,
                "reasoning_chain": reasoning_chain,
                "tool_calls": tool_calls,
                "tool_results": tool_results,
                "context_used": context,
                "confidence_score": confidence_score,
                "session_id": session_id,
                "beliefs_snapshot": self.beliefs.get_belief_summary(),
            }
        except Exception as e:
            print(f"[process_query] 发生异常: {e}", file=sys.stderr)
            return {
                "response": f"I apologize, but I encountered an issue processing your question. As I always say, it's better to be approximately right than precisely wrong. Could you please rephrase your question? Error: {str(e)}",
                "reasoning_chain": ["Error occurred during processing"],
                "tool_calls": [],
                "tool_results": [],
                "context_used": "",
                "confidence_score": 0.1,
                "session_id": session_id,
                "error": str(e),
            }

    def update_market_context(self, news_summary: str) -> Dict:
        """
        根据新闻摘要更新市场信念。
        """
        updates = self.beliefs.update_beliefs_from_news(news_summary)
        return {
            "updates_made": updates,
            "current_beliefs": self.beliefs.get_belief_summary(),
        }

    def get_news_about_symbols(
        self, symbols: List[str], time_range: int = 30
    ) -> List[str]:
        start_date = (datetime.now() - timedelta(time_range)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        print(
            f"[get_news_about_symbols] symbols: {symbols}, date: {start_date}~{end_date}",
            file=sys.stderr,
        )
        news_list = self.fin_data.get_news_from_finnhub(symbols, start_date, end_date)
        if news_list:
            for single_news in tqdm(
                news_list, desc="beliefs from news", file=sys.stderr
            ):
                _ = self.beliefs.update_beliefs_from_news(single_news)
        else:
            print("No news found for the given symbols.", file=sys.stderr)

    def get_portfolio_analysis(self, symbols: List[str]) -> Dict:
        """
        对一组股票做综合分析，返回评分和建议。同时更新市场信念。
        """
        self.get_news_about_symbols(symbols)
        analysis = self.fin_data.get_portfolio_analysis_metrics(symbols)

        for tick_info in analysis:
            symbol, metrics = tick_info.items()
            buffett_score = self.tools.buffett_score(**metrics)

            analysis[symbol] = {
                "buffett_score": buffett_score,
                "recommendation": buffett_score["rating"],
                "key_factors": buffett_score["factors"],
            }

        return analysis
