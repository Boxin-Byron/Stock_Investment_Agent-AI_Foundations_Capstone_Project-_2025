import gradio as gr
import pandas as pd
import random
import time
import requests
import json
import os
import sys
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 中文字体
plt.rcParams['axes.unicode_minus'] = False

# API配置
API_CONFIG = {
    "stock_eval": "http://localhost:8000/api/stock_eval",
    "timeout": 30
}

def call_stock_eval_api(stock_code):
    """调用后端股票评估API"""
    try:
        print(f"开始分析股票 {stock_code}...")
        
        # 尝试查询参数格式
        response = requests.post(
            f"{API_CONFIG['stock_eval']}?stock_code={stock_code}",
            timeout=API_CONFIG["timeout"]
        )
        
        # 尝试form-data格式
        if response.status_code == 422:
            print("尝试使用form-data格式...")
            response = requests.post(
                API_CONFIG["stock_eval"],
                data={"stock_code": stock_code},
                timeout=API_CONFIG["timeout"]
            )
        
        # 尝试直接传递字符串
        if response.status_code == 422:
            print("尝试直接传递字符串...")
            response = requests.post(
                API_CONFIG["stock_eval"],
                json=stock_code,
                headers={"Content-Type": "application/json"},
                timeout=API_CONFIG["timeout"]
            )
        
        response.raise_for_status()
        result = response.json()
        
        return {
            "kline_data": {
                "score": result.get("industry_score", 0),
                "highlights": result.get("kline_summary", []),
                "recommendation": result.get("recommendation", "中性")
            },
            "sentiment_data": {
                "sentiment_score": result.get("sentiment_score", 0),
                "key_events": result.get("key_events", [])
            }
        }
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败：后端服务可能未启动")
        return {
            "kline_data": mock_kline_data(stock_code),
            "sentiment_data": mock_news_sentiment(stock_code)
        }
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP错误 {e.response.status_code}: {e.response.text}")
        return {
            "kline_data": mock_kline_data(stock_code),
            "sentiment_data": mock_news_sentiment(stock_code)
        }
    except Exception as e:
        print(f"❌ 股票评估API调用失败: {e}")
        return {
            "kline_data": mock_kline_data(stock_code),
            "sentiment_data": mock_news_sentiment(stock_code)
        }

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
            None, "", "", "请输入有效的股票代码"
        ]
    
    try:
        print(f"🔍 开始分析股票: {stock_code}")
        
        eval_result = call_stock_eval_api(stock_code)
        kline_data = eval_result["kline_data"]
        sentiment_data = eval_result["sentiment_data"]
        
        prediction = generate_prediction_chart(stock_code)
        
        formatted_kline = format_kline_display(kline_data)
        formatted_sentiment = format_sentiment_display(sentiment_data)
        
        recommendation = generate_investment_recommendation(
            kline_data, sentiment_data, prediction
        )
        
        print(f"✅ 分析完成: {stock_code}")
        
        return [
            formatted_kline,
            formatted_sentiment,
            prediction["chart"],
            prediction["direction"],
            prediction["change_rate"],
            recommendation
        ]
        
    except Exception as e:
        print(f"❌ 股票分析失败: {e}")
        return [
            {"error": f"分析失败: {str(e)}"},
            {"error": f"分析失败: {str(e)}"},
            None, "分析失败", "N/A", "系统错误，请重试"
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
            
            with gr.Column(variant="panel"):
                gr.Markdown("### 💡 综合投资建议")
                recommendation_output = gr.Textbox(
                    show_label=False,
                    interactive=False,
                    scale=1,
                    elem_classes="gap-sm"
                )

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

if __name__ == "__main__":
    print("🚀 启动智能股票分析系统...")
    print("📋 请确保 monitor.py 服务已在 http://localhost:8000 启动")
    print("🔗 前端将在 http://127.0.0.1:7860 启动")
    
    app.launch(
        server_port=7860, 
        share=False,
        inbrowser=True, 
        server_name="127.0.0.1"
    )