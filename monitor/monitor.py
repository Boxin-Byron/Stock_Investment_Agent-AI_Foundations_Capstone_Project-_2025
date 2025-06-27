import os
import random
import datetime
import requests
from fastapi import HTTPException,Request,FastAPI
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
import json
import time
import re
import csv
import sqlite3
import contextlib
from pydantic import BaseModel
from pathlib import Path

# 定义请求体的数据结构
class UserDecisionRequest(BaseModel):
    user_id: str               # 用户ID
    stock_code: str            # 股票代码
    prediction_trend: str      # 预测趋势（"看涨" / "看跌"）
    decision: str              # 用户决策（"willing" / "not willing"）


def get_db_path():
    """智能获取数据库路径"""
    # 1. 检查环境变量
    env_path = os.getenv("DB_PATH")
    if env_path:
        return env_path
    
    # 2. 容器中使用/app/data路径
    return "/app/data/user_preferences.db"  # Docker容器中的路径


DB_PATH = get_db_path()
print(f"📂 使用数据库路径: {DB_PATH}")

def init_db():
    """初始化数据库并确保目录存在"""
    db_path = Path(DB_PATH)
    
    # 确保目录存在
    db_dir = db_path.parent
    if not db_dir.exists():
        db_dir.mkdir(parents=True, exist_ok=True)
        print(f"📂 创建数据库目录: {db_dir}")
    
    # 创建数据库文件（如果不存在）
    if not db_path.exists():
        print(f"🔧 初始化新数据库: {DB_PATH}")
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        stock_code TEXT NOT NULL,
                        prediction_trend TEXT,
                        decision TEXT NOT NULL,
                        decision_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_user_id 
                    ON user_preferences(user_id);
                ''')
                conn.commit()
            print(f"✅ 数据库初始化成功")
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
    else:
        print(f"ℹ️ 使用现有数据库: {DB_PATH}")
    
# Initialize database when module is loaded
init_db()


# 从环境变量获取配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DIFY_FLOW_API_KEY = os.getenv("DIFY_FLOW_API_KEY")

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


def get_user_investment_style(user_id: str):
    """修复后的用户投资风格分析函数"""
    # 忽略默认用户
    if not user_id or user_id == "default_user":
        return ""
    
    try:
        print(f"🔍 重新查询用户偏好: user_id={user_id}")
        
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            with contextlib.closing(conn.cursor()) as cursor:
                # 获取所有决策类型，而不仅是'willing'
                cursor.execute('''
                    SELECT decision, prediction_trend
                    FROM user_preferences 
                    WHERE user_id = ?
                ''', (user_id,))
                rows = cursor.fetchall()
        
        print(f"ℹ️ 找到 {len(rows)} 条用户决策记录")
        
        if not rows:
            return ""
        
        # 统计不同类型决策的比例
        decision_types = {
            "bullish": 0,  # 看涨决策
            "bearish": 0,  # 看跌决策
            "neutral": 0   # 中立决策
        }
        
        for row in rows:
            decision = row['decision']
            trend = row['prediction_trend'] or ""
            
            if "看涨" in trend and decision == "willing":
                decision_types['bullish'] += 1
            elif "看跌" in trend and decision == "willing":
                decision_types['bearish'] += 1
            else:
                decision_types['neutral'] += 1
                
        # 计算各类决策比例
        total = sum(decision_types.values())
        if total == 0:
            return ""
            
        bullish_ratio = decision_types['bullish'] / total
        bearish_ratio = decision_types['bearish'] / total
        neutral_ratio = decision_types['neutral'] / total
        
        print(f"📊 决策比例: 看涨 {bullish_ratio:.1%}, 看跌 {bearish_ratio:.1%}, 中立 {neutral_ratio:.1%}")
        
        # 判断用户风格
        if bullish_ratio > 0.65 and bearish_ratio < 0.2:
            return "我偏好趋势投资，喜欢在上涨行情中买入"
        elif bearish_ratio > 0.65 and bullish_ratio < 0.2:
            return "我倾向于价值投资，市场下跌时寻找抄底机会"
        elif neutral_ratio > 0.7:
            return "我通常保持中立态度，偏向观望市场走势"
        else:
            return "我的投资风格比较平衡，会根据市场情况灵活调整"
            
    except Exception as e:
        print(f"❌ 分析用户偏好错误: {e}")
        return ""


@app.get("/api/user_preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """从数据库获取用户决策历史"""
    try:
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            with contextlib.closing(conn.cursor()) as cursor:
                cursor.execute('''
                    SELECT id, user_id, stock_code, prediction_trend, decision, decision_time 
                    FROM user_preferences 
                    WHERE user_id = ?
                    ORDER BY decision_time DESC
                ''', (user_id,))
                rows = cursor.fetchall()
                
                if not rows:
                    return {"message": "未找到用户偏好记录"}
                
                return [dict(row) for row in rows]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")

@app.post("/api/user_decision")
async def save_user_decision(decision: UserDecisionRequest):
    """保存用户投资决策到数据库"""
    try:
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            with contextlib.closing(conn.cursor()) as cursor:
                cursor.execute('''
                    INSERT INTO user_preferences (user_id, stock_code, prediction_trend, decision)
                    VALUES (?, ?, ?, ?)
                ''', (decision.user_id, decision.stock_code, decision.prediction_trend, decision.decision))
                conn.commit()
        return {"status": "success", "message": "决策保存成功"}
    
    except sqlite3.Error as e:
        return {"status": "error", "message": f"数据库错误: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"系统错误: {str(e)}"}



def call_dify_flow(stock_code: str,user_id: str = "default_user"):
    """调用K线分析微服务，返回latest_metrics字典"""
    headers = {
        'Authorization': f'Bearer {DIFY_FLOW_API_KEY}',
        'Content-Type': 'application/json',
    }
    preference_prompt = get_user_investment_style(user_id)
    base_query = '为我分析这支股票'
    final_query = f"{base_query}。{preference_prompt}" if preference_prompt else base_query
    
    if preference_prompt:
        print(f"👤 根据用户历史记录，添加了偏好描述: {preference_prompt}")
    else:
        print("👤 未检测到用户偏好，使用默认分析。")
    json_data = {
        'inputs': {
            'stock_code': str(stock_code),
        },
        'query': final_query, # 使用构建好的最终query
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
    tech_score = 0.0
    tech_weight = 0.0

    # RSI
    rsi = metrics.get('daily_technical_indicators', {}).get('rsi')
    if rsi is not None:
        rsi_weight = 0.3
        rsi_dist  = min(abs(rsi - 30), abs(rsi - 70))
        rsi_score = max(0, 1 - rsi_dist / 20)
        tech_score += rsi_score * rsi_weight
        tech_weight += rsi_weight

    # MACD
    macd_diff = metrics.get('daily_technical_indicators', {}).get('macd_diff')
    macd_dea  = metrics.get('daily_technical_indicators', {}).get('macd_dea')
    if macd_diff is not None and macd_dea is not None:
        macd_weight = 0.25
        macd_score  = 1 if macd_diff > macd_dea else 0.5
        tech_score += macd_score * macd_weight
        tech_weight += macd_weight

    # 价格变化率
    price_change = metrics.get('price_change_pct') or 0.0
    price_weight = 0.2
    price_score  = 0.5 + price_change * 0.1
    price_score  = max(0, min(1, price_score))
    tech_score  += price_score * price_weight
    tech_weight += price_weight

    # 布林带
    boll_ind = metrics.get('daily_technical_indicators', {})
    close_price = metrics.get('close') or 0.0
    boll_upper  = boll_ind.get('boll_upper') or 0.0
    boll_lower  = boll_ind.get('boll_lower') or 0.0
    if boll_upper > 0 and boll_lower > 0:
        boll_weight = 0.25
        boll_mid    = (boll_upper + boll_lower) / 2
        boll_score  = 0.5 + (close_price - boll_mid) / (boll_upper - boll_mid) * 0.5
        boll_score  = max(0, min(1, boll_score))
        tech_score += boll_score * boll_weight
        tech_weight += boll_weight

    # 新闻情绪
    sentiment       = news_result.get('sentiment_score', 0.0)
    sentiment_score = (sentiment + 1) / 2

    # 综合
    if tech_weight > 0:
        normalized = tech_score / tech_weight
        total      = normalized * 0.7 + sentiment_score * 0.3
    else:
        total = sentiment_score

    # 映射到 5-9 分
    return round(5 + total * 4, 1)


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
    """处理Dify流输出，增强容错性"""
    try:
        # 检查输入是否为空或None
        if not dify_flow_output or 'answer' not in dify_flow_output:
            print("⚠️ Dify输出为空或缺少answer字段")
            return [
                {"error": "Dify输出为空"},
                {"error": "新闻分析失败"},
                {"error": "综合分析失败"}
            ]
        
        input_string = dify_flow_output['answer']
        if not input_string or input_string.strip() == "":
            print("⚠️ Dify返回的answer字段为空")
            return [
                {"error": "Dify返回内容为空"},
                {"error": "新闻分析失败"},
                {"error": "综合分析失败"}
            ]
        
        print(f"📝 Dify原始输出: {input_string[:200]}...")
        
        # 清理字符串
        string = input_string.replace("\n", "").strip()
        
        # 如果不包含JSON分隔符，可能是纯文本回答
        if "}{"  not in string:
            print("⚠️ Dify输出不包含预期的JSON格式")
            return [
                {"raw_content": string},
                {"error": "格式解析失败"},
                {"error": "分析失败"}
            ]
        
        str_list = string.split("}{")
        
        # 确保我们有足够的部分
        if len(str_list) < 3:
            print(f"⚠️ 分割后只有{len(str_list)}个部分，期望3个")
            # 补齐缺失的部分
            while len(str_list) < 3:
                str_list.append('{"error": "数据缺失"}')
        
        # 重新构建完整的JSON字符串
        str_list[0] += "}"
        for i in range(1, len(str_list) - 1):
            str_list[i] = "{" + str_list[i] + "}"
        str_list[-1] = "{" + str_list[-1]
        
        new_list = []
        for i, item in enumerate(str_list[:3]):  # 只处理前3个
            try:
                # 直接加载为JSON对象
                parsed_item = json.loads(item)
                
                # 特别处理第一个字典(latest_metrics)
                if 'latest_metrics' in parsed_item:
                    try:
                        # 尝试解析latest_metrics字符串
                        if isinstance(parsed_item['latest_metrics'], str):
                            parsed_item['latest_metrics'] = json.loads(parsed_item['latest_metrics'])
                    except json.JSONDecodeError as inner_e:
                        print(f"⚠️ latest_metrics解析失败: {inner_e}")
                        # 如果无法解析，保持原始格式
                        pass
                    
                new_list.append(parsed_item)
                print(f"✅ 成功解析第{i+1}个JSON对象")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析错误 (第{i+1}个): {e} | 原始内容: {item[:100]}...")
                # 如果无法解析为JSON，创建错误对象
                new_list.append({
                    "error": f"JSON解析失败: {str(e)}",
                    "raw_content": item[:100] + "..." if len(item) > 100 else item
                })
        
        return new_list
        
    except Exception as main_e:
        print(f"❌ 处理输出失败: {main_e}")
        print(f"❌ 异常类型: {type(main_e).__name__}")
        
        # 备用解析方案
        try:
            if dify_flow_output and 'answer' in dify_flow_output:
                input_string = dify_flow_output['answer']
                return [
                    {"raw_content": input_string[:200] + "..." if len(input_string) > 200 else input_string},
                    {"error": "主解析失败，使用备用方案"},
                    {"error": f"分析失败: {type(main_e).__name__}"}
                ]
        except Exception as backup_e:
            print(f"❌ 备用解析也失败: {backup_e}")
        
        # 最终兜底方案
        return [
            {"error": "完全解析失败"},
            {"error": "新闻分析不可用"},
            {"error": "综合分析不可用"}
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
    """测试网络连接状况（针对中国大陆优化）"""
    test_urls = [
        "https://www.baidu.com",
        "https://httpbin.org/status/200",  # 简单的HTTP测试
        "https://api.dify.ai"  # Dify API服务
    ]
    
    results = {}
    for url in test_urls:
        try:
            start = time.time()
            # 禁用代理以避免连接问题
            response = requests.head(url, timeout=10, verify=False, 
                                   proxies={'http': '', 'https': ''})
            latency = round((time.time() - start) * 1000, 2)
            results[url] = {
                "status_code": response.status_code,
                "latency_ms": latency,
                "accessible": True
            }
        except Exception as e:
            results[url] = {
                "error": str(e),
                "accessible": False
            }
    
    return results


@app.post("/api/stock_eval")
async def stock_eval(request: Request):
    try:
        # 支持两种方式：JSON body 和 查询参数
        try:
            body = await request.json()
            stock_code = body.get("stock_code")
            user_id = body.get("user_id", "default_user")
        except:
            # 如果 JSON 解析失败，尝试从查询参数获取
            stock_code = request.query_params.get("stock_code")
            user_id = request.query_params.get("user_id", "default_user")
            body = {"stock_code": stock_code, "user_id": user_id}

        # 输入预处理
        stock_code = filter_sensitive_words(str(stock_code))
        user_id = filter_sensitive_words(str(user_id))

        if not is_safe_input(stock_code) or not is_safe_input(user_id) or len(stock_code) != 6:
            raise HTTPException(status_code=400, detail="输入包含非法字符")

        print(f"📬 收到请求: {request.method} {request.url}")
        print(f"📥 收到请求体: {body}")
        print(f"📊 分析股票: {stock_code}, 用户ID: {user_id}")
        
        # 确保stock_code是字符串类型且不为None
        if not stock_code:
            raise HTTPException(status_code=400, detail="缺少股票代码参数")
        stock_code = str(stock_code).strip()
        
        if contains_chinese(stock_code):
            temp_code = get_stock_code_with_deepseek(stock_code)
            stock_code = str(temp_code) if temp_code else stock_code

        dify_flow_output = call_dify_flow(stock_code, user_id)  # 正确：传递当前用户的user_id

        print(f"📦 Dify Flow 输出: {dify_flow_output}")
        processed_data = process_dify_flow_outputs(dify_flow_output)
        print(f"🔍 处理后的数据: {processed_data}")

        # 安全地提取各部分数据
        kline_result = processed_data[0] if len(processed_data) > 0 else {}
        news_result_raw = processed_data[1] if len(processed_data) > 1 else {}
        assistant_result = processed_data[2] if len(processed_data) > 2 else {}
        
        # 处理新闻结果
        news_result = {}
        try:
            if (news_result_raw and 
                isinstance(news_result_raw, dict) and 
                'data' in news_result_raw and 
                isinstance(news_result_raw['data'], dict)):
                
                data_obj = news_result_raw['data']
                if ('outputs' in data_obj and 
                    isinstance(data_obj['outputs'], dict)):
                    
                    outputs_obj = data_obj['outputs']
                    if 'text' in outputs_obj:
                        text = str(outputs_obj['text']).replace('```json', '').replace('```', '').strip()
                        text = re.sub(r'\n\s*', '', text)  # 去除换行和多余空格
                        news_result = json.loads(text) # 输出 key_events 列表
                    else:
                        print("⚠️ 新闻结果缺少text字段")
                        news_result = {"error": "新闻数据格式错误"}
                else:
                    print("⚠️ 新闻结果缺少outputs字段")
                    news_result = {"error": "新闻数据格式错误"}
            else:
                print("⚠️ 新闻结果缺少data字段或格式错误")
                news_result = {"error": "新闻数据不可用"}
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"❌ 新闻结果解析失败: {e}")
            news_result = {"error": f"新闻解析失败: {str(e)}"}
        print(f"📈 K线分析结果: {kline_result}")
        print(f"📰 新闻分析结果: {news_result}")
        print(f"🤖 助手分析结果: {assistant_result}")

        # 处理助手分析结果（可能是字符串或字典）
        if isinstance(assistant_result, str):
            try:
                # 尝试将字符串解析为字典
                assistant_result = json.loads(assistant_result)
            except:
                # 如果解析失败，手动转换为带分析文本的字典
                assistant_result = {"分析过程": assistant_result, "最终投资建议": assistant_result}
        # ==== 修复结束 ==== #
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
            # 提取情绪分数和关键事件
            sentiment_score = news_result.get('sentiment_score', 0.0)
            key_events = news_result.get('key_events', [])
        
        print(f"📰 新闻情绪: {sentiment_score}, 关键事件: {key_events}")

        # 处理助手分析数据
        assistant_analysis = ""
        if assistant_result:
            try:
                if isinstance(assistant_result, dict) and '分析过程' in assistant_result and '最终投资建议' in assistant_result:
                    # 确保最终投资建议是字典类型
                    final_recommendation = assistant_result.get('最终投资建议', {})
                    if isinstance(final_recommendation, dict):
                        assistant_analysis = {
                            "analysis_process": assistant_result.get('分析过程', ''),
                            "tech_summary": final_recommendation.get('技术面总结', ''),
                            "news_summary": final_recommendation.get('新闻情绪总结', ''),
                            "recommendation_details": final_recommendation.get('综合判断与投资建议', {})
                        }
                    else:
                        # 如果最终投资建议不是字典，使用字符串格式
                        assistant_analysis = {
                            "analysis_process": assistant_result.get('分析过程', ''),
                            "tech_summary": str(final_recommendation),
                            "news_summary": "",
                            "recommendation_details": str(final_recommendation)
                        }
                elif isinstance(assistant_result, dict) and 'raw_content' in assistant_result:
                    # 对于无法解析的内容，返回原始文本
                    assistant_analysis = {"raw_analysis": assistant_result['raw_content']}
                else:
                    assistant_analysis = {"error": "未获取到有效分析"}
            except Exception as parse_error:
                print(f"❌ 助手分析解析失败: {parse_error}")
                assistant_analysis = {"error": f"解析失败: {str(parse_error)}"}
                final_recommendation = assistant_result.get('最终投资建议', '')
                # 使用正则表达式提取分析内容   
                tech_summary = re.search(r'### 技术面总结(.*?)### 新闻情绪总结', text, re.DOTALL)
                sentiment_summary = re.search(r'### 新闻情绪总结(.*?)### 综合判断与投资建议', text, re.DOTALL)
                investment_suggestion = re.search(r'### 综合判断与投资建议(.*)', text, re.DOTALL)
                # 提取结果
                if tech_summary and sentiment_summary and investment_suggestion:
                    tech_summary = tech_summary.group(1).strip()
                    sentiment_summary = sentiment_summary.group(1).strip()
                    investment_suggestion = investment_suggestion.group(1).strip()
                else:
                    tech_summary = ''
                    sentiment_summary = ''
                    investment_suggestion = ''
                assistant_analysis = {
                    "analysis_process": assistant_result.get('分析过程', ''),
                    "tech_summary": tech_summary,
                    "news_summary": sentiment_summary,
                    "recommendation_details": investment_suggestion
                }

        print(f"🤖 助手分析: {assistant_analysis}")
        
        # 确保metrics是字典类型
        if not isinstance(metrics, dict):
            print(f"⚠️ metrics不是字典类型: {type(metrics)}, 使用默认值")
            metrics = {}
        
        # 确保news_result是字典类型
        if not isinstance(news_result, dict):
            print(f"⚠️ news_result不是字典类型: {type(news_result)}, 使用默认值")
            news_result = {}
        
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


SENSITIVE_WORDS = [
    "习近平", "法轮功", "六四", "天安门", "新疆", "西藏", "港独", "台独", "暴力", "恐怖", "色情", "赌博",
    "delete", "drop", "truncate", "update", "insert", "select", "union", "sleep", "--", ";", "/*", "*/"
]

def filter_sensitive_words(text: str) -> str:
    """替换敏感词为***"""
    for word in SENSITIVE_WORDS:
        text = text.replace(word, "***")
    return text

def is_safe_input(text: str) -> bool:
    # 禁止SQL注入常用符号
    if re.search(r"[;'\"]|--|/\*|\*/", text):
        return False
    # 只允许字母、数字、下划线（可根据实际调整）
    if not re.match(r"^[\w\-]+$", text):
        return False
    return True


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)