import os
import random
import datetime
from fastapi import FastAPI
import requests
from fastapi import HTTPException,Request
from openai import OpenAI
import unicodedata
from fastapi.middleware.cors import CORSMiddleware
import json
import time
import re

# 从环境变量获取配置

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-653829eacd30417996f70834039c0414")
DIFY_FLOW_API_KEY = os.getenv("DIFY_FLOW_API_KEY", "app-Pmqm52DKmWlzsTi07I3uQbSn")

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


def call_dify_flow(stock_code):
    """调用K线分析微服务，返回latest_metrics字典"""
    headers = {
        'Authorization': f'Bearer {DIFY_FLOW_API_KEY}',
        'Content-Type': 'application/json',
    }
    json_data = {
        'inputs': {
            'stock_code': str(stock_code),
        },
        'query': '为我分析这支股票',
        'response_mode': 'blocking',
        'user': 'abc-123',
    }
    # proxies = {
    #     "http": "http://127.0.0.1:7890",
    #     "https": "http://127.0.0.1:7890"
    # }
    try:
        print(f"🌐 请求URL: https://api.dify.ai/v1/chat-messages")
        print(f"📝 请求头: {headers}")
        print(f"📦 请求体: {json_data}")
    #    response = requests.post('https://api.dify.ai/v1/chat-messages', headers=headers, json=json_data,proxies=proxies)
        response = requests.post('https://api.dify.ai/v1/chat-messages', headers=headers, json=json_data)
        response.raise_for_status()
        # 返回格式为 {"latest_metrics": latest_metrics_string}
        return response.json()
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        # 建议添加重试逻辑
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # response = requests.post('https://api.dify.ai/v1/chat-messages', headers=headers, json=json_data,proxies=proxies)
                response = requests.post('https://api.dify.ai/v1/chat-messages', headers=headers, json=json_data)
                response.raise_for_status()
                return response.json()
            except:
                time.sleep(2 ** attempt)
        # 添加回退数据结构
        return {
            "latest_metrics": {"error": "服务不可用"},
            "answer": json.dumps([
                {'latest_metrics': {'error': '服务不可用'}},
                {'data': {'outputs': {'text': json.dumps({'error': '新闻分析失败'})}}},
                {'error': '分析服务不可用'}
            ])
        }
    


def calculate_comprehensive_score(metrics: dict, news_result: dict) -> float:
    """计算综合评分"""
    # 技术指标权重
    tech_score = 0
    tech_weight = 0
    
    # RSI影响
    rsi = metrics.get('daily_technical_indicators', {}).get('rsi')
    if rsi is not None:
        rsi_weight = 0.3
        # RSI在30-70之间最好，离50越远分数越低
        rsi_dist = min(abs(rsi - 30), abs(rsi - 70))
        rsi_score = max(0, 1 - rsi_dist / 20)  # 距离边界20点以内线性递减
        tech_score += rsi_score * rsi_weight
        tech_weight += rsi_weight
    
    # MACD影响
    macd_diff = metrics.get('daily_technical_indicators', {}).get('macd_diff')
    macd_dea = metrics.get('daily_technical_indicators', {}).get('macd_dea')
    if macd_diff is not None and macd_dea is not None:
        macd_weight = 0.25
        macd_score = 1 if macd_diff > macd_dea else 0.5  # 金叉看涨
        tech_score += macd_score * macd_weight
        tech_weight += macd_weight
    
    # 价格变化率影响
    price_change = metrics.get('price_change_pct', 0)
    price_weight = 0.2
    price_score = 0.5 + price_change * 0.1  # 每1%变化影响0.1分
    tech_score += max(0, min(1, price_score)) * price_weight
    tech_weight += price_weight
    
    # 布林带位置影响
    close_price = metrics.get('close')
    boll_upper = metrics.get('daily_technical_indicators', {}).get('boll_upper')
    boll_lower = metrics.get('daily_technical_indicators', {}).get('boll_lower')
    if close_price and boll_upper and boll_lower:
        boll_weight = 0.25
        boll_mid = (boll_upper + boll_lower) / 2
        boll_score = 0.5 + (close_price - boll_mid) / (boll_upper - boll_mid) * 0.5
        tech_score += max(0, min(1, boll_score)) * boll_weight
        tech_weight += boll_weight
    
    # 新闻情绪影响
    sentiment = news_result.get('sentiment_score', 0)
    sentiment_weight = 0.5
    sentiment_score = (sentiment + 1) / 2  # 从[-1,1]映射到[0,1]
    
    # 综合评分 (技术指标占70%，新闻情绪占30%)
    if tech_weight > 0:
        normalized_tech_score = tech_score / tech_weight
        total_score = normalized_tech_score * 0.7 + sentiment_score * 0.3
    else:
        total_score = sentiment_score
    
    # 映射到5-9分范围
    return round(5 + total_score * 4, 1)

def generate_explanation(metrics: dict, news_result: dict) -> dict:
    """生成解释文本和推荐"""
    # 初始化解释部分
    explanation = {
        "kline_analysis": [],
        "recommendation": None
    }
    
    # 1. 添加技术指标解释
    signals = metrics.get('technical_signals', {})
    if signals:
        explanation["kline_analysis"].append("📊 技术分析:")
        if signals.get('rsi_signal'):
            explanation["kline_analysis"].append(f"- RSI指标: {signals['rsi_signal']}")
        if signals.get('macd_signal'):
            explanation["kline_analysis"].append(f"- MACD指标: {signals['macd_signal']}")
        if signals.get('boll_signal'):
            explanation["kline_analysis"].append(f"- 布林带: {signals['boll_signal']}")
    
    # 2. 添加价格变动解释
    price_change = metrics.get('price_change_pct')
    if price_change is not None:
        trend = "上涨" if price_change > 0 else "下跌"
        explanation["kline_analysis"].append(f"📈 最新价格变动: {trend} {abs(price_change):.2f}%")
    
    # 3. 添加新闻情绪解释
    sentiment = news_result.get('sentiment_score')
    if sentiment is not None:
        sentiment_label = "积极" if sentiment > 0.2 else "消极" if sentiment < -0.2 else "中性"
        explanation["kline_analysis"].append(f"📰 新闻情绪: {sentiment_label} ({sentiment:.2f})")
    
    # 4. 生成推荐
    score = calculate_comprehensive_score(metrics, news_result)
    if score >= 8:
        explanation["recommendation"] = "强烈推荐买入"
    elif score >= 7:
        explanation["recommendation"] = "推荐买入"
    elif score >= 5:
        explanation["recommendation"] = "谨慎持有"
    else:
        explanation["recommendation"] = "建议观望"
    
    return explanation

def process_dify_flow_outputs(dify_flow_output):
    try:
        input_string = dify_flow_output['answer']
        string = input_string.replace("\n", "")
        str_list = string.split("}{")
        
        # 确保我们有三个独立字典
        str_list[0] += "}"
        str_list[1] = "{" + str_list[1] + "}"
        str_list[2] = "{" + str_list[2]
        
        new_list = []
        for item in str_list:
            try:
                # 直接加载为JSON对象
                parsed_item = json.loads(item)
                
                # 特别处理第一个字典(latest_metrics)
                if 'latest_metrics' in parsed_item:
                    try:
                        # 尝试解析latest_metrics字符串
                        if isinstance(parsed_item['latest_metrics'], str):
                            parsed_item['latest_metrics'] = json.loads(parsed_item['latest_metrics'])
                    except json.JSONDecodeError:
                        # 如果无法解析，保持原始格式
                        pass
                    
                new_list.append(parsed_item)
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e} | 原始内容: {item}")
                # 如果无法解析为JSON，作为纯文本存入
                new_list.append({"raw_content": item})
        return new_list
    except:
        print(f"处理输出失败: {e}")
        # 添加备用解析方案
        try:
            if "latest_metrics" in input_string:
                start = input_string.find("{", input_string.find("latest_metrics"))
                end = input_string.find("}", start) + 1
                metrics = json.loads(input_string[start:end])
                # ...类似处理其他部分
            return [metrics, news, analysis] if all else []
        except:
            return [
                {"raw_content": input_string[:100] + "..."},
                {"error": "解析失败"},
                {"error": "分析失败"}
            ]
@app.get("/health")
async def health_check():
    print(f"🏥 健康检查: {datetime.datetime.now().isoformat()}")
    return {
        "status": "ok",
        "service": "stock-monitor",
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/api/network_test")
def network_test():
    """测试网络连接状况"""
    test_urls = [
        "https://api.dify.ai", 
        "https://www.baidu.com",
        "https://www.google.com"
    ]
    
    results = {}
    for url in test_urls:
        try:
            start = time.time()
            response = requests.head(url, timeout=5)
            latency = round((time.time() - start) * 1000, 2)
            results[url] = {
                "status_code": response.status_code,
                "latency_ms": latency
            }
        except Exception as e:
            results[url] = {"error": str(e)}
    
    return results


@app.post("/api/stock_eval")
def stock_eval(stock_code: str,request: Request):
    # client_host = request.client.host if request.client else "unknown"
    # print(f"📥 收到请求 from {client_host}: {request.url}")
    try:
        print(f"📊 分析股票: {stock_code}")
        if contains_chinese(stock_code):
            stock_code = get_stock_code_with_deepseek(stock_code)

        dify_flow_output = call_dify_flow(stock_code)
        processed_data = process_dify_flow_outputs(dify_flow_output)
        kline_result = processed_data[0]
        news_result = processed_data[1]
        text = news_result['data']['outputs']['text'].replace('```json', '').replace('```', '').strip()
        text = re.sub(r'\n\s*', '', text)  # 去除换行和多余空格
        news_result = json.loads(text) # 输出 key_events 列表
        assistant_result = processed_data[2]
        print(f"📈 K线分析结果: {kline_result}")
        print(f"📰 新闻分析结果: {news_result}")
        print(f"🤖 助手分析结果: {assistant_result}")
        # 处理技术指标数据
        metrics = {}
        if kline_result and 'latest_metrics' in kline_result:
            if isinstance(kline_result['latest_metrics'], dict):
                metrics = kline_result['latest_metrics']
            elif isinstance(kline_result['latest_metrics'], str):
                try:
                    metrics = json.loads(kline_result['latest_metrics'])
                except:
                    metrics = {}
        
        print(f"📈 技术指标: {metrics}")
        # 获取情绪分析数据
        sentiment_score = 0.0
        key_events = []
        if news_result:
            sentiment_score = news_result.get('sentiment_score', 0.0)
            key_events = news_result.get('key_events', [])
        
        print(f"📰 新闻情绪: {sentiment_score}, 关键事件: {key_events}")
        # 处理助手分析数据
        assistant_analysis = ""
        if assistant_result:
            if '分析过程' in assistant_result and '最终投资建议' in assistant_result:
                # 结构化返回助手分析的详细信息
                assistant_analysis = {
                    "analysis_process": assistant_result.get('分析过程', ''),
                    "tech_summary": assistant_result.get('最终投资建议', {}).get('技术面总结', ''),
                    "news_summary": assistant_result.get('最终投资建议', {}).get('新闻情绪总结', ''),
                    "recommendation_details": assistant_result.get('最终投资建议', {}).get('综合判断与投资建议', {})
                }
            elif 'raw_content' in assistant_result:
                # 对于无法解析的内容，返回原始文本
                assistant_analysis = {"raw_analysis": assistant_result['raw_content']}
            else:
                assistant_analysis = {"error": "未获取到有效分析"}

        print(f"🤖 助手分析: {assistant_analysis}")
        # 计算综合评分
        score = calculate_comprehensive_score(metrics, news_result) if news_result else 0.0
        print(f"🔢 综合评分: {score}")
        # 生成解释文本
        explanation = generate_explanation(metrics, news_result) if news_result else {
            "kline_analysis": ["未获取到技术分析数据"],
            "recommendation": "无法评估"
        }
        print(f"📜 解释文本: {explanation}")
        return {
            "industry_score": score,
            "kline_summary": explanation.get("kline_analysis", []),
            "sentiment_score": sentiment_score,
            "key_events": key_events,
            "recommendation": explanation.get("recommendation", "无法评估"),
            "assistant_analysis": assistant_analysis,
            # 返回原始数据便于调试
            "raw_kline": kline_result,
            "raw_news": news_result,
            "raw_assistant": assistant_result
        }
    except Exception as e:
        print(f"股票分析失败: {str(e)}")
        timestamp = datetime.datetime.now().isoformat()
        return {
            "industry_score": 0.0,
            "kline_summary": [f"分析失败: {str(e)[:100]}"],
            "sentiment_score": 0.0,
            "key_events": [],
            "recommendation": "无法评估",
            "assistant_analysis": {
                "error": str(e),
                "timestamp": timestamp
            },
            "raw_data": {"error_info": str(e)}
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)