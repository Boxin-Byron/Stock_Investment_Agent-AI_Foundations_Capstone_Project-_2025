# frontend/app.py （兼容Gradio 4.x+ 并修复中文显示）
import gradio as gr
import pandas as pd
import random
import time
from datetime import datetime, timedelta

# --------------- 新增：解决中文显示问题 ---------------
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体显示中文
plt.rcParams['axes.unicode_minus'] = False    # 正常显示负号


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

def generate_prediction_chart(stock_code):
    """生成价格预测图表（带中文标题）"""
    base_price = random.randint(30, 100)
    dates = [(datetime.now() + timedelta(days=i)).strftime("%m-%d") for i in range(7)]
    prices = [round(base_price * (1 + 0.02*i) + random.uniform(-1,1), 2) for i in range(7)]
    
    df = pd.DataFrame({"日期": dates, "价格": prices})
    
    # 创建图表（确保中文字体生效）
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

# ------------------------- 主处理逻辑 -------------------------
def analyze_stock(stock_code):
    time.sleep(0.8)  # 模拟API延迟
    
    # 生成模拟数据
    kline_data = mock_kline_data(stock_code)
    sentiment_data = mock_news_sentiment(stock_code)
    prediction = generate_prediction_chart(stock_code)
    
    # 生成投资建议
    buy_signal = prediction["direction"].startswith("看涨") and kline_data["score"] > 6.5
    recommendation = "推荐买入 💹" if buy_signal else "建议持有 ⏸️" if kline_data["score"] > 5 else "考虑卖出 🚨"
    
    return [
        kline_data, 
        sentiment_data, 
        prediction["chart"], 
        prediction["direction"], 
        prediction["change_rate"], 
        recommendation
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
    app.launch(server_port=7860, share=True)
