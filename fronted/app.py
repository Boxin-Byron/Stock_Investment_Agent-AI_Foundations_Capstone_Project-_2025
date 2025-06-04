# frontend/app.py （兼容Gradio 4.x+ 并修复中文显示）
import gradio as gr
import pandas as pd
import random
import time
from datetime import datetime, timedelta

# ------------------------- 配置参数 -------------------------
DIFY_HOST = "http://127.0.0.1:5001"  # 根据实际Dify部署地址修改

# --------------- 新增：解决中文显示问题 ---------------
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体显示中文
plt.rcParams['axes.unicode_minus'] = False    # 正常显示负号



# ------------------------- 真实数据获取函数 -------------------------
def call_stock_eval(stock_code):
    """调用monitor.py的stock_eval接口获取真实数据"""
    try:
        # 创建完整的API URL
        url = f"{DIFY_HOST}/api/stock_eval"
        
        # 发送请求（POST）
        data = {"stock_code": stock_code}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(data), headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            # 如果API返回错误状态码
            return {
                "industry_score": 0.0,
                "kline_summary": ["无法获取数据"],
                "sentiment_score": 0.0,
                "key_events": ["API请求错误"],
                "recommendation": "未知"
            }
    except Exception as e:
        # 处理网络或其他错误
        print(f"API调用错误: {e}")
        return {
            "industry_score": 0.0,
            "kline_summary": ["网络连接错误"],
            "sentiment_score": 0.0,
            "key_events": [str(e)],
            "recommendation": "未知"
        }

# ------------------------- 模拟数据生成函数 -------------------------
def mock_kline_data(stock_code):
    """模拟 K 线分析数据"""
    return {
        "score": round(random.uniform(0.5, 9.9), 1),
        "highlights": [
            "5日均线呈上升趋势",
            "成交量较上周放大120%",
            f"相对行业指数跑赢{random.uniform(1.0, 5.0):.1f}%"
        ],
        "recommendation": random.choice(["行业领先", "行业中性", "行业观望"])
    }

def mock_news_sentiment(stock_code):
    """模拟新闻情绪分析数据"""
    events = ["新产品发布", "行业政策变化", "财报超预期", "竞争对手风波"]
    return {
        "sentiment_score": round(random.uniform(-1.0, 1.0), 2),
        "key_events": random.sample(events, 2)
    }

# ------------------------- 界面组件（使用新版API）-----------------
def create_analysis_block(title, default_content):
    """创建带边框的分析区块"""
    with gr.Column(variant="panel", min_width=300) as block:
        gr.Markdown(f"### {title}")
        json_display = gr.Json(value=default_content, container=False)
    return block, json_display

def generate_prediction_chart(stock_code, industry_score):
    """生成价格预测图表（使用真实数据中的行业评分作为基础）"""
    try:
        base_price = 50 + industry_score * 10  # 基础价格基于行业评分计算
        dates = [(datetime.now() + timedelta(days=i)).strftime("%m-%d") for i in range(7)]
        
        # 更合理的价格变动模型
        prices = [base_price]
        for i in range(1, 7):
            # 基于行业评分和市场随机因素生成价格
            daily_change = (industry_score - 5) * 0.002 + random.uniform(-0.01, 0.01)
            prices.append(prices[-1] * (1 + daily_change))
        
        # 生成数据框
        df = pd.DataFrame({"日期": dates, "价格": prices})
        
        # 创建中文图表
        fig, ax = plt.subplots(figsize=(8,5))
        df.plot(x="日期", y="价格", kind="line", ax=ax, marker="o")
        ax.set_title(f"{stock_code} 一周价格预测", fontsize=14)
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
        # 图表生成错误处理
        print(f"图表生成错误: {e}")
        fig, ax = plt.subplots(figsize=(8,5))
        ax.text(0.5, 0.5, "图表生成错误", ha='center', va='center', fontsize=14)
        return {
            "direction": "未知",
            "change_rate": "0.00%",
            "chart": fig
        }
# ------------------------- 主处理逻辑 -------------------------
def analyze_stock(stock_code):
    # 获取真实数据
    start_time = time.time()
    real_data = call_stock_eval(stock_code)
    api_time = time.time() - start_time
    
    # 格式化数据用于界面展示
    kline_data = {
        "score": real_data.get("industry_score", 0.0),
        "highlights": real_data.get("kline_summary", ["无数据"]),
        "recommendation": real_data.get("recommendation", "未知")
    }
    
    sentiment_data = {
        "sentiment_score": real_data.get("sentiment_score", 0.0),
        "key_events": real_data.get("key_events", ["无关键事件"])
    }
    
    # 使用真实数据中的行业评分生成预测
    prediction = generate_prediction_chart(stock_code, kline_data["score"])
    
    # 模拟API处理延迟
    if api_time < 0.5:
        time.sleep(0.5 - api_time)
    
    # 返回界面所需的所有数据
    return [
        kline_data, 
        sentiment_data, 
        prediction["chart"], 
        prediction["direction"], 
        prediction["change_rate"], 
        real_data.get("recommendation", "未知")
    ]

# ------------------------- 界面布局（优化样式）--------------------
with gr.Blocks(
    title="智能股票分析系统",
    theme=gr.themes.Soft(primary_hue="sky"),
    css="""
    #main-title { text-align: center; margin-bottom: 10px }
    .panel { border-radius: 12px !important; padding: 15px !important; }
    .gap-sm { margin-top: 10px !important; }
    """
) as app:
    
    # 标题区
    gr.Markdown("# 🚀 智能股票分析系统", elem_id="main-title")
    
    # 输入区
    with gr.Row(variant="panel"):
        stock_input = gr.Textbox(
            label="股票代码输入",
            placeholder="输入A股代码（如：600519 茅台）",
            max_lines=1,
            container=False
        )
        analyze_btn = gr.Button("立即分析", variant="primary", size="md")
    
    # 结果展示区
    with gr.Row(equal_height=True):
        # 左侧分析结果
        with gr.Column(scale=1, min_width=400):
            kline_block, kline_display = create_analysis_block("📈 技术指标分析", mock_kline_data(""))
            news_block, news_display = create_analysis_block("📰 市场情绪分析", mock_news_sentiment(""))
        
        # 右侧图表区
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
            
            with gr.Column(variant="panel"):
                gr.Markdown("### 💡 投资建议")
                recommendation_output = gr.Textbox(
                    show_label=False,
                    interactive=False,
                    scale=1,
                    elem_classes="gap-sm"
                )

    # 事件绑定
    analyze_btn.click(
        fn=analyze_stock,
        inputs=[stock_input],
        outputs=[
            kline_display, 
            news_display, 
            chart_output,
            direction_output,
            change_rate_output,
            recommendation_output
        ]
    )

# ------------------------- 运行应用 -------------------------
if __name__ == "__main__":
    app.launch(
        server_port=7860, 
        share=False,
        inbrowser=True, 
        server_name="127.0.0.1"
    )
