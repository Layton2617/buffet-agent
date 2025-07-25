# from langchain.output_parsers import StructuredOutputParser, ResponseSchema, ListOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os
import json
from langchain.prompts import PromptTemplate
import sys
import yfinance as yf

class LangChainTools:
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
    )

    @staticmethod
    def parse_news_beliefs_with_langchain(news_summary: str, all_beliefs_keys: list) -> list:
        print("[parse_news_beliefs_with_langchain] 输入belief_keys:", all_beliefs_keys[:10], "...", file=sys.stderr)
        print("[parse_news_beliefs_with_langchain] 输入news_summary:", news_summary[:10], "...", file=sys.stderr)
        prompt = PromptTemplate(
            template=(
                "You are a financial news analysis assistant. Please extract all relevant belief objects, sentiments and confidence levels from the news summary below.\n"
                "Reference belief objects: {belief_keys}\n"
                "News summary: {news_summary}\n"
                "Output format (strictly follow this JSON array, do not add extra text):\n"
                "[\n"
                "  {{\"news_key_object\": \"...\", \"news_sentiment\": \"...\", \"news_confidence\": ...}},\n"
                "  ...\n"
                "]\n"
                "Each news_confidence must be a float between 0 and 1, not a string."
            ),
            input_variables=["belief_keys", "news_summary"],
        )
        _input = prompt.format(
            belief_keys=", ".join(all_beliefs_keys), news_summary=news_summary
        )
        print("[parse_news_beliefs_with_langchain] prompt已输入", file=sys.stderr)
        output = LangChainTools.llm.invoke(_input)
        print("[parse_news_beliefs_with_langchain] LLM输出已输出", file=sys.stderr)
        try:
            # 提取第一个 [ ... ] 之间的内容
            if hasattr(output, "content"):
                output = output.content
            start = output.find('[')
            end = output.rfind(']')
            if start != -1 and end != -1:
                json_str = output[start:end+1]
                print("[parse_news_beliefs_with_langchain] 提取到的json字符串：", json_str[:10], "...", file=sys.stderr)
                parsed = json.loads(json_str)
                if isinstance(parsed, list):
                    print(f"[parse_news_beliefs_with_langchain] 成功解析出{len(parsed)}条记录", file=sys.stderr)
                    return parsed
            # fallback: 直接尝试解析
            parsed = json.loads(output)
            if isinstance(parsed, list):
                print(f"[parse_news_beliefs_with_langchain] fallback成功解析出{len(parsed)}条记录", file=sys.stderr)
                return parsed
        except Exception as e:
            print(f"parse_news_beliefs_with_langchain JSON parsing failed: {e}", file=sys.stderr)
        return []

    @staticmethod
    def parse_tickers_with_langchain(message: str) -> list:
        """
        利用大语言模型和结构化解析技术，从自然语言对话中提取股票代码（tickers），包括字面上的和描述性的。
        :param text: 用户输入的自然语言文本
        :return: 股票代码列表
        """
        prompt = PromptTemplate(
            template=(
                "You are a financial assistant. Extract all stock tickers from the following human message, including literal tickers (like AAPL, GOOG).\n"
                "Only return a JSON array of tickers, the format should be like: [\"XXX\", \"YYY\", \"ZZZ\"]\n"
                "Do not add any other text, do not use explanations, and ticker usually is between 2 and 6 characters.\n"
                "Message: {message}"
            ),
            input_variables=["message"],
        )
        _input = prompt.format(message=message)
        try:
            output = LangChainTools.llm.invoke(_input)
            if hasattr(output, "content"):
                output = output.content
            # 提取第一个 [ ... ] 之间的内容
            start = output.find('[')
            end = output.rfind(']')
            if start != -1 and end != -1:
                json_str = output[start:end+1]
                tickers = json.loads(json_str)
                if isinstance(tickers, list):
                    # 去重并过滤空字符串
                    return list({t.strip().upper() for t in tickers if t.strip()})
            # fallback: 直接尝试解析
            tickers = json.loads(output)
            if isinstance(tickers, list):
                return list({t.strip().upper() for t in tickers if t.strip()})
        except Exception as e:
            print(f"LangChain structured ticker parsing failed: {e}")
            # 兜底：用正则提取大写字母ticker
            import re
            return list(set(re.findall(r'\b[A-Z]{1,6}\b', message)))
        return []
    


    def filter_valid_tickers(ticker_list):
        results = LangChainTools.parse_tickers_with_langchain(ticker_list)
        valid = []
        for t in results:
            try:
                time = yf.Ticker(t).info.get("trailingPegRatio")
                print(f"ticker: {t}, time: {time}")
                if time:
                    valid.append(t)
            except Exception:
                continue
        return valid

if __name__ == "__main__":
    # 测试用例：
    # test_news = "Apple reported strong quarterly earnings, with technology sector sentiment positive. There are concerns about geopolitical risk, but overall market sentiment remains optimistic."
    # test_belief_keys = ["AAPL", "technology_disruption", "market_sentiment", "corporate_earnings", "geopolitical_risk"]
    # print("=== 测试 parse_news_beliefs_with_langchain ===")
    # results = LangChainTools.parse_news_beliefs_with_langchain(test_news, test_belief_keys)
    # print("解析结果：")
    # print(results)
    print(LangChainTools.filter_valid_tickers("please analyze AAPL's and GOOGL's DCF, PE, and safety margin"))