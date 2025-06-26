import gradio as gr
import pandas as pd
import random
import time
import requests
import json
import os
import sys
from datetime import datetime, timedelta
import csv
import re

import matplotlib.pyplot as plt
from matplotlib import font_manager
import platform

# 自动适配中英文字体，兼容 Linux 和 Windows，增强健壮性
def setup_chinese_font():
    system = platform.system().lower()
    chinese_font_path = None

    if system == "windows":
        # Windows 常见中文字体
        possible_fonts = [
            "SimHei", "Microsoft YaHei", "SimSun", "Arial Unicode MS"
        ]
        for font in possible_fonts:
            try:
                plt.rcParams['font.sans-serif'] = [font]
                # 测试能否正常显示中文
                plt.figure()
                plt.text(0.5, 0.5, "中文字体测试", fontsize=12)
                plt.close()
                print(f"✅ Windows: 使用字体: {font}")
                break
            except Exception as e:
                continue
        else:
            print("⚠️ Windows: 未找到合适的中文字体，使用默认字体")
    else:
        # Linux 常见中文字体路径
        possible_fonts = [
            '/usr/share/fonts/custom/SimHei.ttf',
            '/usr/share/fonts/custom/SIMFANG.ttf',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc',
            '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc'
        ]
        for font in possible_fonts:
            if os.path.exists(font):
                chinese_font_path = font
                print(f"✅ Linux: 找到字体文件: {font}")
                break
        if chinese_font_path:
            prop = font_manager.FontProperties(fname=chinese_font_path)
            plt.rcParams['font.family'] = prop.get_name()
            plt.rcParams['font.sans-serif'] = [prop.get_name()]
            print(f"🌏 Linux: 设置中文字体: {prop.get_name()}")
        else:
            print("⚠️ Linux: 未找到中文字体文件，使用默认字体")
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']

    plt.rcParams['axes.unicode_minus'] = False

setup_chinese_font()

# ------------------------- 配置参数 -------------------------
DIFY_HOST = os.getenv("DIFY_HOST", "http://monitor:5001")
# 添加模拟模式开关
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

# 增强路径处理 - 使用当前目录下的data文件夹
DATA_DIR = os.path.join(os.getcwd(), "user_data")
os.makedirs(DATA_DIR, exist_ok=True)
print(f"📂 用户数据将保存至: {DATA_DIR}")

def call_stock_eval_api(stock_code):
    """调用后端股票评估API（增强健壮性版本）"""
    try:
        print(f"开始分析股票 {stock_code}...")
        
        url = f"{DIFY_HOST}/api/stock_eval"
        print(f"🔗 调用API: {url}")
        params = {"stock_code": str(stock_code)}
        
        response = requests.post(url, params=params, timeout=120) # 增加超时
        response.raise_for_status()
        
        result = response.json()
        
        # --- 健壮性处理核心 ---
        assistant_analysis = result.get("assistant_analysis", {})

        # 1. 如果后端返回的是字符串，尝试解析为JSON
        if isinstance(assistant_analysis, str):
            print("⚠️ 后端返回的 assistant_analysis 是字符串，尝试解析...")
            try:
                # 清理可能的Markdown代码块标记
                cleaned_str = assistant_analysis.strip().removeprefix("```json").removesuffix("```").strip()
                assistant_analysis = json.loads(cleaned_str)
            except json.JSONDecodeError:
                print("❌ 解析 assistant_analysis 字符串失败，将作为纯文本处理。")
                # 解析失败，保持其为字符串，后续逻辑会处理

        # 2. 初始化所有 assistant_data 字段的默认值
        detailed_recommendation = ""
        analysis_process = "无分析过程"
        tech_summary = "无技术总结"
        news_summary = "无新闻总结"

        # 3. 仅当 assistant_analysis 是字典时，才提取内部字段
        if isinstance(assistant_analysis, dict):
            analysis_process = assistant_analysis.get("analysis_process", "无分析过程")
            tech_summary = assistant_analysis.get("tech_summary", "无技术总结")
            news_summary = assistant_analysis.get("news_summary", "无新闻总结")
            
            rec_details = assistant_analysis.get("recommendation_details")
            
            if isinstance(rec_details, dict):
                # 提取主要逻辑证据
                evidence = (
                    rec_details.get('支持逻辑') or
                    rec_details.get('主要逻辑证据') or
                    rec_details.get('支持该判断的主要逻辑证据', '无')
                ).replace('；', '\n  - ')

                # 提取潜在风险
                risks = (
                    rec_details.get('风险提示') or
                    rec_details.get('潜在风险提示', '无')
                ).replace('；', '\n  - ')

                # 提取未来趋势
                future_trend = (
                    rec_details.get('未来一周趋势方向') or
                    rec_details.get('对未来一周的趋势方向及可能变动幅度估计')
                )
                if not future_trend:
                    trend_direction = rec_details.get('对未来一周趋势方向', '')
                    amplitude = rec_details.get('可能变动幅度', '')
                    future_trend = f"{trend_direction}{amplitude}" if amplitude else trend_direction
                future_trend = future_trend or '无'

                detailed_recommendation = (
                    f"👉 当前建议: {rec_details.get('当前建议', '无')}\n"
                    f"📅 未来一周趋势: {future_trend}\n"
                    f"🔎 主要支持证据:\n  - {evidence}\n"
                    f"⚠️ 潜在风险:\n  - {risks}"
                )
            else:
                # 如果是字典但没有 recommendation_details，则美化输出整个字典
                detailed_recommendation = json.dumps(assistant_analysis, indent=2, ensure_ascii=False)
        else:
            # 如果不是字典（例如，解析失败的字符串），直接显示它
            detailed_recommendation = str(assistant_analysis)
        
        return {
            "kline_data": {
                "score": result.get("industry_score", 0),
                "highlights": result.get("kline_summary", []),
                "recommendation": result.get("recommendation", "中性")
            },
            "sentiment_data": {
                "sentiment_score": result.get("sentiment_score", 0),
                "key_events": result.get("key_events", [])
            },
            "assistant_data": {
                "detailed_recommendation": detailed_recommendation,
                "analysis_process": analysis_process,
                "tech_summary": tech_summary,
                "news_summary": news_summary
            }
        }
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接失败：无法连接到后端服务 at {DIFY_HOST} - {e}")
        # 抛出自定义异常，以便在UI上显示更友好的信息
        raise ConnectionError(f"无法连接到后端分析服务({DIFY_HOST})，请检查后端服务是否正常运行。") from e
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP错误 {e.response.status_code}: {e.response.text}")
        # 抛出自定义异常，以便在UI上显示更友好的信息
        raise ValueError(f"后端服务返回错误: {e.response.status_code}") from e
    except Exception as e:
        print(f"❌ 股票评估API调用失败: {e}")
        # 重新抛出异常，以便上层捕获
        raise e

def mock_kline_data(stock_code):
    """模拟K线分析数据"""
    mock_scores = {
        "600519": 8.5,
        "000001": 6.2,
        "000002": 4.1,
        "600000": 7.2,
        "000858": 5.8,
        "002415": 6.9,
    }
    
    score = mock_scores.get(stock_code, round(random.uniform(3.0, 9.0), 1))
    
    return {
        "score": score,
        "highlights": [
            f"技术评分: {score}/10",
            "5日均线呈上升趋势" if score > 6 else "均线走势偏弱",
            f"成交量较上周放大{random.randint(80, 200)}%",
            f"相对行业指数{'跑赢' if score > 5 else '跑输'}{random.uniform(1.0, 5.0):.1f}%"
        ],
        "recommendation": (
            "行业领先" if score >= 7.5 
            else "行业中性" if score >= 5.0 
            else "行业观望"
        )
    }

def mock_news_sentiment(stock_code):
    """模拟新闻情绪分析数据"""
    mock_sentiments = {
        "600519": 0.7,
        "000001": 0.1,
        "000002": -0.3,
        "600000": 0.4,
        "000858": -0.1,
        "002415": 0.6,
    }
    
    sentiment = mock_sentiments.get(stock_code, round(random.uniform(-0.8, 0.8), 2))
    
    positive_events = ["财报超预期", "新产品发布", "行业政策利好", "机构增持"]
    negative_events = ["竞争加剧", "监管收紧", "业绩下滑", "高管变动"]
    neutral_events = ["行业会议", "分析师覆盖", "股东大会", "定期报告"]
    
    if sentiment > 0.3:
        events = random.sample(positive_events, 2)
    elif sentiment < -0.3:
        events = random.sample(negative_events, 2)
    else:
        events = random.sample(neutral_events + positive_events[:2], 2)
    
    return {
        "sentiment_score": sentiment,
        "key_events": events
    }

def mock_assistant_analysis(stock_code):
    """模拟AI助手详细分析"""
    mock_analyses = {
        "600519": {
            "当前建议": "买入",
            "对未来一周的趋势方向及可能变动幅度估计": "预计上涨3-5%",
            "支持该判断的主要逻辑证据": "业绩稳定增长；品牌价值持续提升；白酒行业复苏明显",
            "潜在风险提示": "估值偏高；消费环境不确定性；行业竞争加剧"
        },
        "000001": {
            "当前建议": "持有",
            "对未来一周的趋势方向及可能变动幅度估计": "震荡整理，变动幅度±2%",
            "支持该判断的主要逻辑证据": "金融改革受益；资产质量改善；估值相对合理",
            "潜在风险提示": "利率环境变化；信贷风险；监管政策不确定性"
        }
    }
    
    default_analysis = {
        "当前建议": random.choice(["买入", "持有", "卖出"]),
        "对未来一周的趋势方向及可能变动幅度估计": f"预计{'上涨' if random.random() > 0.5 else '下跌'}{random.randint(1, 8)}%",
        "支持该判断的主要逻辑证据": "技术面向好；基本面稳定；市场情绪积极",
        "潜在风险提示": "市场波动；政策变化；业绩不确定性"
    }
    
    analysis = mock_analyses.get(stock_code, default_analysis)
    
    # 构建详细建议字符串
    detailed_recommendation = (
        f"👉 当前建议: {analysis['当前建议']}\n"
        f"📅 未来一周趋势: {analysis['对未来一周的趋势方向及可能变动幅度估计']}\n"
        f"🔎 主要支持证据:\n  - {analysis['支持该判断的主要逻辑证据'].replace('；', chr(10) + '  - ')}\n"
        f"⚠️ 潜在风险:\n  - {analysis['潜在风险提示'].replace('；', chr(10) + '  - ')}"
    )
    
    return {
        "detailed_recommendation": detailed_recommendation,
        "analysis_process": f"模拟分析过程：基于对 {stock_code} 的模拟技术指标和新闻情绪，我们得出了以下结论。这是一个模拟的分析过程，用于测试目的。",
        "tech_summary": "模拟技术总结：模拟的均线系统显示多头排列，模拟的RSI指标处于中性区域。整体技术面模拟为中性偏多。",
        "news_summary": "模拟新闻总结：近期无重大模拟新闻事件。市场情绪模拟为中性。"
    }

def get_stock_data(stock_code, use_mock=False):
    """统一的数据获取函数，根据模式选择真实数据或模拟数据"""
    if use_mock:
        print(f"🎭 使用模拟数据模式分析: {stock_code}")
        return {
            "kline_data": mock_kline_data(stock_code),
            "sentiment_data": mock_news_sentiment(stock_code),
            "assistant_data": mock_assistant_analysis(stock_code)
        }
    else:
        print(f"🌐 使用真实数据模式分析: {stock_code}")
        return call_stock_eval_api(stock_code)

def format_kline_display(kline_data, tech_summary=None):
    """格式化K线数据为字符串"""
    score = kline_data.get("score", 0)
    highlights = kline_data.get("highlights", [])
    recommendation = kline_data.get("recommendation", "中性")
    
    highlights_str = "\n".join([f"  - {item}" for item in highlights])
    
    tech_summary_str = f"\n\n📝 技术总结:\n{tech_summary}" if tech_summary and "无技术总结" not in tech_summary else ""
    
    return (
        f"📊 综合评分: {score:.1f}/10\n"
        f"⭐ 评级: {get_rating_by_score(score)}\n"
        f"💡 分析师建议: {recommendation}\n"
        f"🔍 技术亮点:\n{highlights_str}"
        f"{tech_summary_str}"
    )

def format_sentiment_display(sentiment_data, news_summary=None):
    """格式化情绪数据为字符串"""
    sentiment_score = sentiment_data.get("sentiment_score", 0)
    key_events = sentiment_data.get("key_events", [])
    
    events_str = "\n".join([f"  - {item}" for item in key_events])

    news_summary_str = f"\n\n📝 新闻总结:\n{news_summary}" if news_summary and "无新闻总结" not in news_summary else ""

    return (
        f"😊 情绪指数: {sentiment_score:.2f}\n"
        f"📈 情绪趋势: {get_sentiment_trend(sentiment_score)}\n"
        f"🎯 市场关注度: {get_attention_level(sentiment_score, key_events)}\n"
        f"📰 关键事件:\n{events_str}"
        f"{news_summary_str}"
    )

def get_rating_by_score(score):
    if score is None: score = 0
    if score >= 8.0:
        return "⭐⭐⭐⭐⭐ 强烈推荐"
    elif score >= 6.5:
        return "⭐⭐⭐⭐ 推荐"
    elif score >= 5.0:
        return "⭐⭐⭐ 中性"
    elif score >= 3.0:
        return "⭐⭐ 谨慎"
    else:
        return "⭐ 回避"

def get_sentiment_trend(sentiment_score):
    if sentiment_score > 0.5:
        return "🚀 非常乐观"
    elif sentiment_score > 0.2:
        return "📈 偏向乐观"
    elif sentiment_score > -0.2:
        return "➡️ 中性观望"
    elif sentiment_score > -0.5:
        return "📉 偏向悲观"
    else:
        return "⚠️ 非常悲观"

def get_attention_level(sentiment_score, key_events):
    event_count = len(key_events) if key_events else 0
    sentiment_abs = abs(sentiment_score)
    
    attention_score = event_count * 0.3 + sentiment_abs * 0.7
    
    if attention_score > 0.8:
        return "🔥 高度关注"
    elif attention_score > 0.5:
        return "👀 中度关注"
    elif attention_score > 0.2:
        return "📝 一般关注"
    else:
        return "😴 关注较少"

def generate_prediction_chart(stock_code, assistant_data):
    """根据AI助手的分析，生成更智能的价格预测图表"""
    try:
        # 默认值
        trend_direction = "震荡"
        change_min, change_max = 1.0, 2.0 # 默认震荡幅度

        # 从 assistant_data 中提取趋势预测文本
        recommendation_text = assistant_data.get("detailed_recommendation", "")
        trend_text_line = ""
        for line in recommendation_text.split('\n'):
            if "未来一周趋势" in line:
                trend_text_line = line.strip()
                break
        
        # 解析趋势和幅度
        if "上涨" in trend_text_line:
            trend_direction = "上涨"
        elif "下跌" in trend_text_line:
            trend_direction = "下跌"
        
        numbers = [float(n) for n in re.findall(r'\d+\.?\d*', trend_text_line)]
        if len(numbers) >= 2:
            change_min, change_max = min(numbers), max(numbers)
        elif len(numbers) == 1:
            change_min = change_max = numbers[0]

        # 生成价格数据
        base_price = random.randint(30, 100)
        dates = [(datetime.now() + timedelta(days=i)).strftime("%m-%d") for i in range(7)]
        prices = [base_price]
        
        if trend_direction == "上涨":
            total_change_percent = random.uniform(change_min, change_max) / 100.0
        elif trend_direction == "下跌":
            total_change_percent = -random.uniform(change_min, change_max) / 100.0
        else: # 震荡
            total_change_percent = random.uniform(-change_max, change_max) / 100.0

        # 生成平滑但有随机性的路径
        for i in range(1, 7):
            daily_target_price = base_price * (1 + total_change_percent * (i / 6))
            noise = random.uniform(-0.01, 0.01) * base_price # 1%的日内波动
            next_price = daily_target_price + noise
            prices.append(round(next_price, 2))

        df = pd.DataFrame({"日期": dates, "价格": prices})
        
        fig, ax = plt.subplots(figsize=(8,5))
        df.plot(x="日期", y="价格", kind="line", ax=ax, marker="o", color="green" if trend_direction == "上涨" else "red" if trend_direction == "下跌" else "grey")
        ax.set_title("未来一周价格预测 (基于AI分析)", fontsize=14)
        ax.set_xlabel("日期", fontsize=12)
        ax.set_ylabel("价格 (元)", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        
        return {
            "direction": "看涨 ▲" if prices[-1] > prices[0] else "看跌 ▼",
            "change_rate": f"{(prices[-1]/prices[0]-1)*100:.2f}%",
            "chart": fig
        }
    except Exception as e:
        print(f"生成图表失败: {e}")
        # 创建错误图表
        fig, ax = plt.subplots(figsize=(8,5))
        ax.text(0.5, 0.5, "图表生成失败\n请检查数据", 
                ha="center", va="center", fontsize=14)
        ax.set_title("图表错误", color="red")
        return {
            "direction": "错误",
            "change_rate": "N/A",
            "chart": fig
        }

def generate_investment_recommendation(kline_data, sentiment_data, prediction):
    """生成综合投资建议"""
    score = kline_data.get("score", 0)
    sentiment_score = sentiment_data.get("sentiment_score", 0)
    is_bullish = prediction["direction"].startswith("看涨")
    
    # 综合评分权重：技术50%，情绪30%，价格趋势20%
    composite_score = (
        score * 0.5 + 
        (sentiment_score + 1) * 5 * 0.3 +
        (8 if is_bullish else 2) * 0.2
    )
    
    if composite_score >= 7.5:
        return "🚀 强烈推荐买入 - 多项指标显示积极信号"
    elif composite_score >= 6.0:
        return "📈 建议买入 - 技术面和基本面均表现良好"
    elif composite_score >= 4.5:
        return "⏸️ 建议持有 - 保持观望，等待更明确信号"
    elif composite_score >= 3.0:
        return "⚠️ 考虑减仓 - 存在一定下行风险"
    else:
        return "🚨 建议卖出 - 多项指标显示负面信号"

def save_user_preference(preference, analysis_context):
    """将用户的投资偏好和分析上下文保存到文件中"""
    if not preference:
        return "⚠️ 请先做出选择", gr.update(visible=True)

    stock_code = analysis_context.get("stock_code", "N/A")
    prediction_direction = analysis_context.get("prediction", {}).get("direction", "N/A")
    
    # 添加时间戳确保唯一性
    timestamp = datetime.now().strftime('%Y-%m-%d')
    filename = f"user_preferences_{timestamp}.csv"
    filepath = os.path.join(DATA_DIR, filename)
    
    # 写入CSV文件
    try:
        file_exists = os.path.exists(filepath)
        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['时间', '股票代码', '预测趋势', '用户偏好'])
            
            writer.writerow([
                datetime.now().strftime('%H:%M:%S'),
                stock_code,
                prediction_direction,
                preference
            ])
        
        print(f"✅ 用户偏好已保存至: {filepath}")
        message = f"✅ 感谢反馈！数据保存于: {filepath}\n您可以点击下方'浏览用户数据'查看"
        return message, gr.update(visible=False)
    except Exception as e:
        print(f"❌ 保存用户偏好失败: {e}")
        return f"❌ 保存失败: {e}", gr.update(visible=True)

def get_saved_user_prefs():
    """获取所有保存的用户偏好文件"""
    try:
        # 获取目录下所有CSV文件
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
        
        # 按修改时间排序（最新在前）
        files.sort(key=lambda x: os.path.getmtime(os.path.join(DATA_DIR, x)), reverse=True)
        
        return files
    except Exception as e:
        print(f"❌ 获取用户偏好文件列表失败: {e}")
        return []

def create_analysis_block(title, default_content):
    """创建分析区块"""
    with gr.Column(variant="panel", min_width=300) as block:
        gr.Markdown(f"### {title}")
        text_display = gr.Textbox(
            value=default_content,
            lines=8,
            max_lines=15,
            interactive=False,
            show_label=False,
            container=False
        )
    return block, text_display

def analyze_stock(stock_code, use_mock_data):
    """主分析函数 - 流式输出版本"""
    if not stock_code.strip():
        yield [
            gr.update(value="错误: 请输入股票代码"),
            gr.update(value="错误: 请输入股票代码"),
            None, "", "", "", 
            gr.update(value="错误: 请输入股票代码"),
            gr.update(visible=False),
            {}
        ]
        return

    # 初始加载状态
    outputs = [
        "分析中...",  # kline_display
        "分析中...",  # news_display
        None,  # chart_output
        "...",  # direction_output
        "...",  # change_rate_output
        "...",  # short_recommendation
        "分析中...",  # detailed_recommendation
        gr.update(visible=False),  # feedback_box
        {}  # analysis_context_state
    ]
    yield outputs

    try:
        print(f"🔍 开始分析股票: {stock_code}")
        
        is_fallback = False
        try:
            eval_result = get_stock_data(stock_code, use_mock=use_mock_data)
        except Exception as e:
            print(f"❌ 股票分析失败，自动切换到模拟模式: {e}")
            if not use_mock_data:
                print("🔄 尝试使用模拟数据...")
                eval_result = get_stock_data(stock_code, use_mock=True)
                is_fallback = True
            else:
                raise e

        # --- 数据准备 ---
        kline_data = eval_result["kline_data"]
        sentiment_data = eval_result["sentiment_data"]
        assistant_data = eval_result.get("assistant_data", {})
        
        prediction = generate_prediction_chart(stock_code, assistant_data)
        kline_text = format_kline_display(kline_data, assistant_data.get("tech_summary"))
        sentiment_text = format_sentiment_display(sentiment_data, assistant_data.get("news_summary"))
        short_recommendation_text = generate_investment_recommendation(
            kline_data, sentiment_data, prediction
        )
        
        # 组合分析过程和详细建议
        analysis_process_text = assistant_data.get("analysis_process", "")
        detailed_recommendation_text = assistant_data.get(
            "detailed_recommendation", "未获取到详细分析"
        )
        
        # 如果有分析过程，就把它加在详细建议前面
        if analysis_process_text and "无分析过程" not in analysis_process_text:
            detailed_recommendation_text = f"🧠 分析过程:\n{analysis_process_text}\n\n{detailed_recommendation_text}"

        if is_fallback:
            detailed_recommendation_text += f"\n\n⚠️ 注意：因后端服务异常，已自动切换至模拟数据模式。"

        # --- 更新静态UI部分 ---
        outputs[2] = prediction["chart"]
        outputs[3] = prediction["direction"]
        outputs[4] = prediction["change_rate"]
        outputs[5] = short_recommendation_text
        
        # --- 流式输出 ---
        max_len = max(len(kline_text), len(sentiment_text), len(detailed_recommendation_text))
        for i in range(max_len):
            if i < len(kline_text):
                outputs[0] = kline_text[:i+1]
            if i < len(sentiment_text):
                outputs[1] = sentiment_text[:i+1]
            if i < len(detailed_recommendation_text):
                outputs[6] = detailed_recommendation_text[:i+1]
            
            yield outputs
            time.sleep(0.01)

        # --- 最终状态 ---
        analysis_context = {
            "stock_code": stock_code,
            "prediction": prediction
        }
        outputs[7] = gr.update(visible=True)
        outputs[8] = analysis_context
        yield outputs

    except Exception as e:
        print(f"❌ 分析彻底失败: {e}")
        error_msg = f"分析失败: {str(e)}"
        yield [
            gr.update(value=error_msg),
            gr.update(value=error_msg),
            None, "分析失败", "N/A", "系统错误，请重试", "详细分析获取失败",
            gr.update(visible=False),
            {}
        ]

# 界面布局
with gr.Blocks(
    title="智能股票分析系统",
    theme=gr.themes.Soft(primary_hue="sky"),
    css="""
    #main-title { text-align: center; margin-bottom: 10px }
    .panel { border-radius: 12px !important; padding: 15px !important; }
    .gap-sm { margin-top: 10px !important; }
    """
) as app:
    
    analysis_context_state = gr.State({})

    gr.Markdown("# 🚀 智能股票分析系统", elem_id="main-title")
    gr.Markdown("### 💡 支持股票代码或中文名称输入（如：600519 或 贵州茅台）")
    
    with gr.Row(variant="panel"):
        with gr.Column(scale=3):
            stock_input = gr.Textbox(
                label="股票代码/名称输入",
                placeholder="输入A股代码（如：600519）或中文名称（如：贵州茅台）",
                max_lines=1,
                container=False
            )
        with gr.Column(scale=1):
            # 添加数据模式选择
            mock_data_checkbox = gr.Checkbox(
                label="使用模拟数据",
                value=USE_MOCK_DATA,
                info="勾选此选项将使用模拟数据进行分析"
                # visible=False  # 隐藏此开关
            )
        with gr.Column(scale=1):
            analyze_btn = gr.Button("🔍 立即分析", variant="primary", size="md")
    
    # 显示当前模式
    mode_status = gr.Markdown(
        value=f"🎭 当前模式: {'模拟数据模式' if USE_MOCK_DATA else '真实数据模式'}"
        #visible=False # 隐藏模式状态显示
    )
    
    with gr.Row(equal_height=True):
        with gr.Column(scale=1, min_width=400):
            kline_block, kline_display = create_analysis_block(
                "📈 技术指标分析", 
                format_kline_display(mock_kline_data(""))
            )
            news_block, news_display = create_analysis_block(
                "📰 市场情绪分析", 
                format_sentiment_display(mock_news_sentiment(""))
            )
        
        with gr.Column(scale=2):
            with gr.Column(variant="panel"):
                gr.Markdown("### 📊 价格预测趋势")
                chart_output = gr.Plot(label="price_chart", show_label=False)
                
                with gr.Row():
                    direction_output = gr.Textbox(
                        label="趋势方向",
                        interactive=False,
                        scale=1,
                        elem_classes="gap-sm"
                    )
                    change_rate_output = gr.Textbox(
                        label="预期涨幅",
                        interactive=False,
                        scale=1,
                        elem_classes="gap-sm"
                    )
            
            # 修改投资建议区块为双建议面板
            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Column(variant="panel"):
                        gr.Markdown("### 💡 AI投资建议")
                        short_recommendation = gr.Textbox(
                            show_label=False,
                            interactive=False,
                            container=False
                        )
                
                with gr.Column(scale=1):
                    with gr.Column(variant="panel"):
                        gr.Markdown("### 📝 详细建议说明")
                        detailed_recommendation = gr.Textbox(
                            show_label=False,
                            interactive=False,
                            lines=8,
                            max_lines=15,
                            container=False
                        )
            
            with gr.Column(variant="panel", visible=False) as feedback_box:
                gr.Markdown("### 🤔 您是否愿意根据此分析进行投资？")
                preference_radio = gr.Radio(
                    ["愿意", "中立", "不愿意"], 
                    label="您的选择",
                    container=False
                )
                submit_feedback_btn = gr.Button("提交反馈", variant="secondary")
                feedback_status = gr.Markdown()

    # 更新模式状态显示
    def update_mode_status(use_mock):
        return f"🎭 当前模式: {'模拟数据模式' if use_mock else '真实数据模式'}"
    
    mock_data_checkbox.change(
        fn=update_mode_status,
        inputs=[mock_data_checkbox],
        outputs=[mode_status]
    )

    analyze_btn.click(
        fn=analyze_stock,
        inputs=[stock_input, mock_data_checkbox],  # 添加模拟数据选择作为输入
        outputs=[
            kline_display, 
            news_display, 
            chart_output,
            direction_output,
            change_rate_output,
            short_recommendation,
            detailed_recommendation,
            feedback_box,             # 控制反馈区域的可见性
            analysis_context_state    # 更新状态
        ]
    )

    submit_feedback_btn.click(
        fn=save_user_preference,
        inputs=[preference_radio, analysis_context_state],
        outputs=[feedback_status, feedback_box] # 提交后更新状态文本并隐藏反馈区
    )



# 在应用启动时
def check_resources():
    problems = []
    # 检查数据目录权限
    if not os.access(DATA_DIR, os.W_OK):
        problems.append(f"目录不可写: {DATA_DIR}")
    
    # 检查字体可用性
    try:
        plt.figure()
        plt.text(0.5, 0.5, "字体测试", fontsize=12)
        plt.close()
    except Exception as e:
        problems.append(f"字体错误: {str(e)}")
    
    return problems

# 修改文件末尾的启动代码
if __name__ == "__main__":
    issues = check_resources()
    if issues:
        print("❌ 启动前检查失败:")
        for issue in issues:
            print(f"  - {issue}")
    # Windows 专用处理
    if sys.platform == 'win32':
        print("🛠️ Windows 系统检测 - 启用专用设置")
        os.environ['GRADIO_SERVER_NAME'] = '0.0.0.0'  # 确保在容器内绑定到正确地址
        # Windows Docker 内部容器需要通过 DNS 名称连接
        os.environ['DIFY_HOST'] = "host.docker.internal:5001"
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
        plt.rcParams['axes.unicode_minus'] = False
        print("Using Windows Chinese fonts")

    print("🚀 启动智能股票分析系统...")
    print(f"🔗 DIFY_HOST: {DIFY_HOST}")
    print(f"🌐 服务将在 http://0.0.0.0:7860 启动")
    
    # 创建初始偏好文件示例（如果目录为空）
    if not os.listdir(DATA_DIR):
        sample_file = os.path.join(DATA_DIR, "user_preferences_samples.csv")
        with open(sample_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['时间', '股票代码', '预测趋势', '用户偏好'])
            writer.writerow(['09:30:45', '600519', '看涨 ▲', '愿意'])
            writer.writerow(['10:15:22', '000001', '中性 →', '中立'])
        print(f"📝 创建示例文件: {sample_file}")

    # 强制设置为可外部访问的配置
    app.launch(
        server_name="0.0.0.0",   # 允许所有网络接口访问
        server_port=7860,        # 固定端口
        share=False,
        debug=True               # 显示详细错误
    )
