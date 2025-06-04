from fastapi import FastAPI
import requests
from fastapi import HTTPException
from openai import OpenAI
import unicodedata

# ------------------------- 配置参数 -------------------------
DIFY_HOST = "http://127.0.0.1:5001"  # 根据实际Dify部署地址修改

def get_stock_code_with_deepseek(stock_name: str):
    try:
        client = OpenAI(api_key="sk-653829eacd30417996f70834039c0414", base_url="https://api.deepseek.com")

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个股票信息查询助手。"},
                {"role": "user", "content": f"请问{stock_name}的股票代码是什么？只需要告诉我代码即可，不需要告诉我额外的内容。"},
            ],
            stream=False
        )

        # print(response.choices[0].message.content)
        return response.choices[0].message.content
    except Exception as e:
        # 如果API错误，返回一个常见股票的默认代码
        print(f"DeepSeek API错误: {str(e)}")
        return "000001"  # 默认返回上证指数代码

def contains_chinese(text):
    """检查字符串中是否包含汉字"""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False


def call_kline_flow(stock_code):
    """调用Dify中的K线分析工作流"""
    try:
        url = DIFY_HOST  # K线分析工作流地址
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "input": stock_code
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # 错误处理：返回带有错误信息的模拟数据
        print(f"K线分析API错误: {str(e)}")
        return {
            "score": round(random.uniform(5.0, 9.0), 1),
            "highlights": [f"API错误: {str(e)}"],
            "recommendation": random.choice(["观望", "谨慎操作"])
        }

def call_news_flow(stock_code):
    """调用Dify中的新闻情绪分析工作流"""
    try:
        url = DIFY_HOST  # 新闻情绪分析工作流地址
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "input": stock_code
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # 错误处理：返回带有错误信息的模拟数据
        print(f"新闻情绪分析API错误: {str(e)}")
        return {
            "sentiment_score": round(random.uniform(-0.5, 0.8), 2),
            "key_events": [f"API错误: {str(e)}"]
        }



app = FastAPI()

@app.post("/api/stock_eval")
def stock_eval(stock_code: str):
    if contains_chinese(stock_code):
        stock_code = get_stock_code_with_deepseek(stock_code)
    kline_result = call_kline_flow(stock_code)
    news_result = call_news_flow(stock_code)

    return {
        "industry_score": kline_result.get("score"),
        "kline_summary": kline_result.get("highlights"),
        "sentiment_score": news_result.get("sentiment_score"),
        "key_events": news_result.get("key_events"),
        "recommendation": kline_result.get("recommendation")
    }