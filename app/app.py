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



def call_stock_eval_api(stock_code):
    """调用后端股票评估API"""
    try:
        print(f"开始分析股票 {stock_code}...")
        
       # 创建完整的API URL
        url = f"{DIFY_HOST}/api/stock_eval"
        
        # 修改：将数据作为 URL 查询参数发送，而不是 JSON 请求体
        params = {"stock_code": stock_code}
        
        # 发送请求（POST），使用 params 参数
        # 增加超时时间以应对可能的慢响应
        response = requests.post(url, params=params, timeout=30)
        
        response.raise_for_status()  # 如果状态码不是2xx，将引发HTTPError
        
        result = response.json()
        
        # 获取详细分析数据
        assistant_analysis = result.get("assistant_analysis", {})
        
        # 提取详细分析中的关键信息
        detailed_recommendation = ""  # 初始化为空字符串
        if isinstance(assistant_analysis, dict) and "recommendation_details" in assistant_analysis:
            rec_details = assistant_analysis["recommendation_details"]
            # 单独处理每一项内容
            evidence = rec_details.get('支持该判断的主要逻辑证据', '无').replace('；', '\n  - ')
            risks = rec_details.get('潜在风险提示', '无').replace('；', '\n  - ')
            
            # 构建详细建议字符串
            detailed_recommendation = (
                f"👉 当前建议: {rec_details.get('当前建议', '无')}\n"
                f"📅 未来一周趋势: {rec_details.get('对未来一周的趋势方向及可能变动幅度估计', '无')}\n"
                f"🔎 主要支持证据:\n  - {evidence}\n"
                f"⚠️ 潜在风险:\n  - {risks}"
            )
        else:
            # 其他情况处理
            detailed_recommendation = json.dumps(assistant_analysis, indent=2, ensure_ascii=False)
        
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
                "detailed_recommendation": detailed_recommendation
            }
        }
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接失败：无法连接到后端服务 at {DIFY_HOST}")
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


def format_kline_display(kline_data):
    """格式化K线数据"""
    score = kline_data.get("score", 0)
    highlights = kline_data.get("highlights", [])
    recommendation = kline_data.get("recommendation", "中性")
    
    return {
        "📊 综合评分": f"{score:.1f}/10",
        "🔍 技术亮点": highlights,
        "💡 分析师建议": recommendation,
        "⭐ 评级": get_rating_by_score(score)
    }

def format_sentiment_display(sentiment_data):
    """格式化情绪数据"""
    sentiment_score = sentiment_data.get("sentiment_score", 0)
    key_events = sentiment_data.get("key_events", [])
    
    return {
        "😊 情绪指数": f"{sentiment_score:.2f}",
        "📈 情绪趋势": get_sentiment_trend(sentiment_score),
        "📰 关键事件": key_events,
        "🎯 市场关注度": get_attention_level(sentiment_score, key_events)
    }

def get_rating_by_score(score):
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

def generate_prediction_chart(stock_code):
    """生成价格预测图表"""
    base_price = random.randint(30, 100)
    dates = [(datetime.now() + timedelta(days=i)).strftime("%m-%d") for i in range(7)]
    prices = [round(base_price * (1 + 0.02*i) + random.uniform(-1,1), 2) for i in range(7)]
    
    df = pd.DataFrame({"日期": dates, "价格": prices})
    
    fig, ax = plt.subplots(figsize=(8,5))
    df.plot(x="日期", y="价格", kind="line", ax=ax, marker="o")
    ax.set_title("未来一周价格预测", fontsize=14)
    ax.set_xlabel("日期", fontsize=12)
    ax.set_ylabel("价格 (元)", fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    
    return {
        "direction": "看涨 ▲" if prices[-1] > prices[0] else "看跌 ▼",
        "change_rate": f"{(prices[-1]/prices[0]-1)*100:.2f}%",
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
    
    filename = "user_preferences.csv"
    file_exists = os.path.exists(filename)
    
    try:
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 如果文件是新创建的，则写入表头
            if not file_exists:
                writer.writerow(['timestamp', 'stock_code', 'prediction_direction', 'user_preference'])
            
            # 写入数据
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                stock_code,
                prediction_direction,
                preference
            ])
        
        print(f"✅ 用户偏好已保存: {stock_code} - {preference}")
        # 返回成功信息，并隐藏反馈区域
        return "✅ 感谢您的反馈！", gr.update(visible=False)
    except Exception as e:
        print(f"❌ 保存用户偏好失败: {e}")
        return f"❌ 保存失败: {e}", gr.update(visible=True)


def create_analysis_block(title, default_content):
    """创建分析区块"""
    with gr.Column(variant="panel", min_width=300) as block:
        gr.Markdown(f"### {title}")
        json_display = gr.Json(value=default_content, container=False)
    return block, json_display

def analyze_stock(stock_code):
    """主分析函数"""
    if not stock_code.strip():
         return [
            {"error": "请输入股票代码"},
            {"error": "请输入股票代码"},
            None, "", "", "", "",
            gr.update(visible=False),  # 隐藏反馈区域
            {}  # 清空状态
        ]
    
    try:
        print(f"🔍 开始分析股票: {stock_code}")
        eval_result = call_stock_eval_api(stock_code)
        
        kline_data = eval_result["kline_data"]
        sentiment_data = eval_result["sentiment_data"]
        assistant_data = eval_result.get("assistant_data", {})
        
        prediction = generate_prediction_chart(stock_code)
        formatted_kline = format_kline_display(kline_data)
        formatted_sentiment = format_sentiment_display(sentiment_data)
        
        short_recommendation = generate_investment_recommendation(
            kline_data, sentiment_data, prediction
        )
        
        detailed_recommendation = assistant_data.get(
            "detailed_recommendation", "未获取到详细分析"
        )
        
        print(f"✅ 分析完成: {stock_code}")
        
        # 准备要传递给反馈环节的上下文
        analysis_context = {
            "stock_code": stock_code,
            "prediction": prediction
        }
        
        return [
            formatted_kline,
            formatted_sentiment,
            prediction["chart"],
            prediction["direction"],
            prediction["change_rate"],
            short_recommendation,
            detailed_recommendation,
            gr.update(visible=True),  # 显示反馈区域
            analysis_context  # 更新状态
        ]
        
    except Exception as e:
        print(f"❌ 股票分析失败: {e}")
        return [
            {"error": f"分析失败: {str(e)}"},
            {"error": f"分析失败: {str(e)}"},
            None, "分析失败", "N/A", "系统错误，请重试", "详细分析获取失败",
            gr.update(visible=False),  # 隐藏反馈区域
            {}  # 清空状态
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
        stock_input = gr.Textbox(
            label="股票代码/名称输入",
            placeholder="输入A股代码（如：600519）或中文名称（如：贵州茅台）",
            max_lines=1,
            container=False
        )
        analyze_btn = gr.Button("🔍 立即分析", variant="primary", size="md")
    
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
                            lines=5,
                            max_lines=10,
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


    analyze_btn.click(
        fn=analyze_stock,
        inputs=[stock_input],
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


# 修改文件末尾的启动代码
if __name__ == "__main__":
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
    
    # 强制设置为可外部访问的配置
    app.launch(
        server_name="0.0.0.0",   # 允许所有网络接口访问
        server_port=7860,        # 固定端口
        share=False,
        debug=True               # 显示详细错误
    )
