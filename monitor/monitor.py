import os
import random
import datetime
from fastapi import FastAPI
import requests
from fastapi import HTTPException
from openai import OpenAI
import unicodedata
from fastapi.middleware.cors import CORSMiddleware


# 从环境变量获取配置
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
NEWS_FLOW_ID = os.getenv("DIFY_NEWS_FLOW_ID")
NEWS_API_KEY = os.getenv("DIFY_NEWS_API_KEY")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

STOCK_ASSISTANT_FLOW_ID = os.getenv('STOCK_ASSISTANT_FLOW_ID')

# 构建工作流调用URL
KLINE_FLOW_URL = "https://stock-investment-agent-ai-foundations.onrender.com/analyze"
NEWS_FLOW_URL = f"{DIFY_BASE_URL}/workflows/run/{NEWS_FLOW_ID}"

app = FastAPI()
# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_stock_code_with_deepseek(stock_name: str):
    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

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
        return {
            "贵州茅台": "600519",
            "腾讯控股": "00700",
            "阿里巴巴": "09988",
        }.get(stock_name, "000001")  # 默认返回上证指数

def contains_chinese(text):
    """检查字符串中是否包含汉字"""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False


def call_kline_flow(stock_code):
    """调用K线分析微服务，返回latest_metrics字典"""
    try:
        # 假设K线分析服务运行在本地8000端口
        url = "http://localhost:8000/analyze"
        payload = {"stock_code": stock_code}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        # 返回格式为 {"latest_metrics": latest_metrics_string}
        return response.json()
    except Exception as e:
        print(f"K线分析服务调用错误: {str(e)}")
        # 返回模拟数据结构
        return {
            "latest_metrics": '{"error": "K线分析服务不可用", "detail": "%s"}' % str(e)
        }

def call_news_flow(stock_code):
    """调用Dify中的新闻情绪分析工作流"""
    try:
        headers = {
            "Authorization": f"Bearer {NEWS_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": stock_code,
            "response_mode": "blocking"
        }
        
        response = requests.post(NEWS_FLOW_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # 错误处理：返回带有错误信息的模拟数据
        print(f"新闻情绪分析API错误: {str(e)}")
        return {
            "sentiment_score": round(random.uniform(-0.5, 0.8), 2),
            "key_events": [f"API错误: {str(e)}"]
        }

def call_dify_stock_assistant(stock_code: str):
    """流式调用Dify股票分析助手Chatflow，返回生成器"""
    try:
        url = f"{DIFY_BASE_URL}/workflows/run/{STOCK_ASSISTANT_FLOW_ID}"
        headers = {
            "Authorization": f"Bearer {os.getSTOCK_ASSISTANT_FLOW_IDenv('STOCK_ASSISTANT_API_KEY')}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": {"stock_code": stock_code},
            "response_mode": "streaming"
        }
        with requests.post(url, json=payload, headers=headers, stream=True, timeout=60) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
    except Exception as e:
        yield f"流式API错误: {str(e)}".encode("utf-8")


@app.get("/health")
async def health_check():
    print(f"🏥 健康检查: {datetime.datetime.now().isoformat()}")
    return {
        "status": "ok",
        "service": "stock-monitor",
        "timestamp": datetime.datetime.now().isoformat()
    }


@app.post("/api/stock_eval")
def stock_eval(stock_code: str):
    print(f"📊 分析股票: {stock_code}")
    if contains_chinese(stock_code):
        stock_code = get_stock_code_with_deepseek(stock_code)
    kline_result = call_kline_flow(stock_code)
    news_result = call_news_flow(stock_code)
    assistant_result = b''.join(call_dify_stock_assistant(stock_code)).decode("utf-8")

    return {
        "stock_code": stock_code,
        "kline_analysis": kline_result.get("latest_metrics", "{}"),
        "news_sentiment": {
            "score": news_result.get("sentiment_score", 0.0),
            "key_events": news_result.get("key_events", [])
        },
        "assistant_analysis": assistant_result
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)