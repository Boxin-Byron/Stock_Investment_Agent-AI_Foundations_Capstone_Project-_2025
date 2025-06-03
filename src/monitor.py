from fastapi import FastAPI
import requests
from fastapi import HTTPException
from openai import OpenAI
import unicodedata

def get_stock_code_with_deepseek(stock_name: str):
    client = OpenAI(api_key="sk-653829eacd30417996f70834039c0414", base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一个股票信息查询助手。"},
            {"role": "user", "content": f"请问{stock_name}的股票代码是什么？只需要告诉我代码即可，不要额外的内容。"},
        ],
        stream=False
    )

    # print(response.choices[0].message.content)
    return response.choices[0].message.content

def contains_chinese(text):
    """检查字符串中是否包含汉字"""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

app = FastAPI()

def call_kline_flow(stock_code):
    return requests.post("http://<dify_host>/api/kline", json={"input": stock_code}).json()

def call_news_flow(stock_code):
    return requests.post("http://<dify_host>/api/news", json={"input": stock_code}).json()

@app.post("/api/stock_eval")
def stock_eval(stock_code: str):
    if contains_chinese(stock_code):
        stock_code = int(get_stock_code_with_deepseek(stock_code))
    kline_result = call_kline_flow(stock_code)
    news_result = call_news_flow(stock_code)

    return {
        "industry_score": kline_result.get("score"),
        "kline_summary": kline_result.get("highlights"),
        "sentiment_score": news_result.get("sentiment_score"),
        "key_events": news_result.get("key_events"),
        "recommendation": kline_result.get("recommendation")
    }