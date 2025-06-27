import gradio as gr
import pandas as pd
import random
import time
import requests
import json
import os
import sys
import math
from datetime import datetime, timedelta
import csv
import re
import matplotlib.pyplot as plt
from matplotlib import font_manager
import platform
from typing import List, Union

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


def call_stock_eval_api(stock_code, params=None):
    """调用后端股票评估API"""
    print(params)
    if params is None:
        params = {}
    try:
        print(f"开始分析股票 {stock_code}...")
        
        url = f"{DIFY_HOST}/api/stock_eval"
        print(f"🔗 调用API: {url} 参数: {params}")
        
        response = requests.post(url, json=params, timeout=120) # 增加超时
        response.raise_for_status()
        
        result = response.json()
        
        # --- 健壮性处理核心 ---
        assistant_analysis = result.get("assistant_analysis", {})

            # 修复解析逻辑的重点部分
        if isinstance(assistant_analysis, dict):
            # 提取基本信息
            analysis_process = assistant_analysis.get("analysis_process", "未提供分析过程")
            tech_summary = assistant_analysis.get("tech_summary", "未提供技术总结")
            news_summary = assistant_analysis.get("news_summary", "未提供新闻总结")
            
            # === 重构建detailed_recommendation ===
            detailed_recommendation = assistant_analysis.get("recommendation_details", "未提供详细建议")
        else:
            # 如果 assistant_analysis 不是字典，使用默认值
            analysis_process = "未提供分析过程"
            tech_summary = "未提供技术总结"
            news_summary = "未提供新闻总结"
            detailed_recommendation = "未提供详细建议"
        


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
    
    tech_summary_str = ""
    # 检查 tech_summary 是否为字典，如果是，则进行格式化
    if isinstance(tech_summary, dict):
        lines = ["\n\n📝 技术总结:"]
        for key, value in tech_summary.items():
            # 如果值是列表，则进一步格式化
            if isinstance(value, list):
                lines.append(f"  - {key}:")
                for item in value:
                    lines.append(f"    - {item}")
            else:
                lines.append(f"  - {key}: {value}")
        tech_summary_str = "\n".join(lines)
    # 如果是普通字符串且不是默认值，则直接使用
    elif isinstance(tech_summary, str) and "无技术总结" not in tech_summary:
        tech_summary_str = f"\n\n📝 技术总结:\n{tech_summary}"
    
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

    news_summary_str = ""
    # 检查 news_summary 是否为字典，如果是，则进行格式化
    if isinstance(news_summary, dict):
        lines = ["\n\n📝 新闻总结:"]
        # 提取情绪倾向
        sentiment_tendency = news_summary.get('总体情绪倾向及得分', '无')
        lines.append(f"  - 情绪倾向: {sentiment_tendency}")
        
        # 提取关键事件 (增强健壮性)
        events_list = news_summary.get('关键事件与潜在影响路径', [])
        if events_list:
            lines.append("  - 关键事件:")
            # 如果 events_list 是一个列表，则遍历它
            if isinstance(events_list, list):
                for event in events_list:
                    lines.append(f"    - {event}")
            # 如果是其他类型（如单个字符串），则直接添加
            else:
                lines.append(f"    - {str(events_list)}")
        news_summary_str = "\n".join(lines)
    # 如果是普通字符串且不是默认值，则直接使用
    elif isinstance(news_summary, str) and "无新闻总结" not in news_summary:
        news_summary_str = f"\n\n📝 新闻总结:\n{news_summary}"

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
        change_min, change_max = 1.0, 3.0
        confidence_level = 0.5  # 置信度
        
        # 多维度信息提取
        recommendation_text = assistant_data.get("detailed_recommendation", "")
        analysis_process = assistant_data.get("analysis_process", "")
        tech_summary = assistant_data.get("tech_summary", "")
        news_summary = assistant_data.get("news_summary", "")
        
        # 综合文本分析
        all_text = f"{recommendation_text} {analysis_process} {tech_summary} {news_summary}".lower()
        
        # 更智能的趋势识别
        trend_score = 0
        trend_keywords = {
            # 看涨关键词及权重
            "上涨": 3, "买入": 3, "看好": 2, "积极": 2, "乐观": 2, "强势": 2,
            "突破": 2, "向上": 1.5, "多头": 2, "利好": 1.5, "推荐": 1,
            "继续上涨": 3, "持续上升": 2.5, "强烈推荐": 3, "增长": 1.5,
            
            # 看跌关键词及权重（负值）
            "下跌": -3, "卖出": -3, "看空": -2, "悲观": -2, "回调": -1.5,
            "跌破": -2, "向下": -1.5, "空头": -2, "利空": -1.5, "减仓": -1,
            "继续下跌": -3, "持续下降": -2.5, "建议卖出": -3, "下滑": -1.5,
            
            # 震荡关键词
            "震荡": 0, "横盘": 0, "整理": 0, "观望": 0, "中性": 0, "持有": 0
        }
        
        # 计算趋势得分
        for keyword, weight in trend_keywords.items():
            count = all_text.count(keyword)
            trend_score += count * weight
            if count > 0:
                confidence_level = min(1.0, confidence_level + count * 0.1)
        
        # 数字提取和分析
        price_numbers = []
        percentage_patterns = [
            r'(\d+\.?\d*)[-~到至]\s*(\d+\.?\d*)%',  # 范围百分比
            r'(\d+\.?\d*)%\s*[-~到至]\s*(\d+\.?\d*)%',
            r'上涨\s*(\d+\.?\d*)%',  # 单独上涨百分比
            r'下跌\s*(\d+\.?\d*)%',  # 单独下跌百分比
            r'涨幅\s*(\d+\.?\d*)%',
            r'跌幅\s*(\d+\.?\d*)%',
            r'变动\s*(\d+\.?\d*)%',
            r'幅度.*?(\d+\.?\d*)%',
        ]
        
        for pattern in percentage_patterns:
            matches = re.findall(pattern, all_text)
            for match in matches:
                if isinstance(match, tuple):
                    price_numbers.extend([float(x) for x in match if x])
                else:
                    price_numbers.append(float(match))
        
        # 价格区间提取
        price_range_patterns = [
            r'(\d+)-(\d+)元',
            r'(\d+)到(\d+)元',
            r'(\d+\.?\d*)-(\d+\.?\d*)',
            r'区间.*?(\d+\.?\d*).*?(\d+\.?\d*)',
        ]
        
        for pattern in price_range_patterns:
            matches = re.findall(pattern, all_text)
            for match in matches:
                try:
                    low, high = float(match[0]), float(match[1])
                    if 1 <= low <= 30 and 1 <= high <= 30:  # 合理的百分比范围
                        price_numbers.extend([low, high])
                except (ValueError, IndexError):
                    continue
        
        # 过滤合理的数字（1-20%的变动范围）
        valid_numbers = [n for n in price_numbers if 0.1 <= n <= 20]
        
        if valid_numbers:
            change_min = min(valid_numbers)
            change_max = max(valid_numbers)
            # 确保最小值不小于0.5%，最大值不超过15%
            change_min = max(0.5, change_min)
            change_max = min(15.0, change_max)
            if change_max <= change_min:
                change_max = change_min + 1.0
        
        # 趋势方向判断
        if trend_score > 2:
            trend_direction = "上涨"
        elif trend_score < -2:
            trend_direction = "下跌"
        else:
            trend_direction = "震荡"
        
        # 根据置信度调整变动幅度
        confidence_multiplier = 0.5 + confidence_level * 0.5  # 0.5-1.0
        change_min *= confidence_multiplier
        change_max *= confidence_multiplier

        # 生成价格数据
        base_price = random.randint(30, 100)
        dates = [(datetime.now() + timedelta(days=i)).strftime("%m-%d") for i in range(7)]
        prices: List[float] = [float(base_price)]
        
        # 根据趋势生成目标变化率
        if trend_direction == "上涨":
            total_change_percent = random.uniform(change_min, change_max) / 100.0
        elif trend_direction == "下跌":
            total_change_percent = -random.uniform(change_min, change_max) / 100.0
        else:  # 震荡
            # 震荡模式：先上涨后下跌或相反
            amplitude = random.uniform(change_min, change_max) / 100.0
            total_change_percent = random.uniform(-amplitude/2, amplitude/2)

        # 生成更真实的价格路径
        volatility = 0.02 * confidence_level  # 基础波动率
        
        if trend_direction == "震荡":
            # 震荡模式：生成波浪形走势
            for i in range(1, 7):
                wave_factor = math.sin(i * math.pi / 3) * 0.01  # 正弦波动
                daily_noise = random.uniform(-volatility, volatility)
                trend_component = total_change_percent * (i / 6)
                
                next_price = base_price * (1 + trend_component + wave_factor + daily_noise)
                prices.append(next_price)
        else:
            # 趋势模式：平滑但有随机波动的路径
            for i in range(1, 7):
                progress = i / 6
                # 非线性趋势进展（先慢后快或先快后慢）
                if trend_direction == "上涨":
                    trend_progress = progress ** 0.8  # 加速上涨
                else:
                    trend_progress = 1 - (1 - progress) ** 0.8  # 加速下跌
                
                daily_target = base_price * (1 + total_change_percent * trend_progress)
                daily_noise = random.uniform(-volatility, volatility) * base_price
                
                next_price = daily_target + daily_noise
                # 确保价格不会过度偏离趋势
                if trend_direction == "上涨":
                    next_price = max(prices[-1] * 0.98, next_price)
                elif trend_direction == "下跌":
                    next_price = min(prices[-1] * 1.02, next_price)
                
                prices.append(next_price)

        # 确保所有价格都是正数且合理
        prices = [max(1.0, price) for price in prices]
        
        df = pd.DataFrame({"日期": dates, "价格": [round(p, 2) for p in prices]})
        
        # 图表绘制
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 根据趋势选择颜色
        line_color = {
            "上涨": "#2E8B57",  # 深绿色
            "下跌": "#DC143C",  # 深红色
            "震荡": "#4682B4"   # 钢蓝色
        }.get(trend_direction, "#696969")
        
        # 绘制价格线
        ax.plot(df["日期"], df["价格"], 
                marker="o", linewidth=2.5, markersize=6, 
                color=line_color, markerfacecolor="white", 
                markeredgecolor=line_color, markeredgewidth=2)
        
        # 添加趋势区域填充
        if trend_direction != "震荡":
            ax.fill_between(df["日期"], df["价格"], 
                          [prices[0]] * len(prices), 
                          alpha=0.2, color=line_color)
        
        # 图表美化
        ax.set_title(f"未来一周价格预测 - {trend_direction}趋势 (置信度: {confidence_level:.1%})", 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel("日期", fontsize=12)
        ax.set_ylabel("价格 (元)", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.3)
        
        # 添加趋势标注
        final_change = (prices[-1] / prices[0] - 1) * 100
        trend_label = f"{trend_direction} {final_change:+.1f}%"
        ax.text(0.02, 0.98, trend_label, transform=ax.transAxes, 
                fontsize=12, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor=line_color, alpha=0.2),
                verticalalignment='top')
        
        plt.tight_layout()
        
        return {
            "direction": f"{trend_direction} {'▲' if final_change > 0 else '▼' if final_change < 0 else '→'}",
            "change_rate": f"{final_change:+.2f}%",
            "chart": fig
        }
        
    except Exception as e:
        print(f"生成图表失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 创建错误图表
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.text(0.5, 0.5, f"图表生成失败\n错误: {str(e)[:50]}...", 
                ha="center", va="center", fontsize=12, color="red")
        ax.set_title("图表生成错误", color="red")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
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

# 删除整个 save_user_preference 函数，用以下代码替代：
def save_user_preference(preference, analysis_context):
    """将用户的投资决策保存到数据库"""
    if not preference:
        return "⚠️ 请先做出选择", gr.update(visible=True)
    # 映射前端选择到后端需要的值
    decision_mapping = {
        "愿意": "willing",
        "不愿意": "not willing",
        "中立": "not willing"  # 中立也视为不愿意
    }
    
    stock_code = analysis_context.get("stock_code", "N/A")
    prediction_direction = analysis_context.get("prediction", {}).get("direction", "N/A")
    
    try:
        # 调用后端的保存接口
        url = f"{DIFY_HOST}/api/user_decision"
        data = {
            "user_id": "web_user",  # 暂时使用固定用户ID
            "stock_code": stock_code,
            "prediction_trend": prediction_direction,
            "decision": decision_mapping.get(preference, "not willing")
        }
        
        response = requests.post(url, json=data, timeout=5)
        response.raise_for_status()
        
        print(f"✅ 用户决策已保存至数据库: {data}")
        return "✅ 感谢您的反馈，决策已保存！", gr.update(visible=False)
    
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return f"❌ 网络错误: {str(e)}", gr.update(visible=True)
    except Exception as e:
        print(f"❌ 保存用户决策失败: {e}")
        return f"❌ 保存失败: {str(e)}", gr.update(visible=True)


def create_analysis_block(title, default_content):
    """创建分析区块"""
    with gr.Column(variant="panel", min_width=300) as block:
        gr.Markdown(f"### {title}")
        text_display = gr.Textbox(
            value=default_content,
            lines=8,
            max_lines=28,
            interactive=False,
            show_label=False,
            container=False
        )
    return block, text_display

def analyze_stock(stock_code, use_mock_data):
    """主分析函数 - 流式输出版本 (已修复)"""
    # 初始化输出
    outputs = [
        "分析中...",            # kline_display
        "分析中...",            # news_display
        None,                  # chart_output
        "分析中...",            # direction_output
        "分析中...",            # change_rate_output
        "分析中...",            # short_recommendation
        "分析中...",            # detailed_recommendation
        gr.update(visible=False),    # feedback_box
        {}                  # analysis_context_state
    ]
    yield outputs
    
    # 处理空输入
    if not stock_code.strip():
        yield outputs
        return
    
    try:
        print(f"🔍 开始分析股票: {stock_code}")
        
        user_id = "web_user"
        eval_result = {}
        error_message = ""
        
        # ==== 获取数据 ====
        try:
            if not use_mock_data:
                params = {"stock_code": stock_code, "user_id": user_id}
                eval_result = call_stock_eval_api(stock_code, params)
            else:
                eval_result = get_stock_data(stock_code, use_mock=True)
                
            if not eval_result:
                raise Exception("未获取到有效的分析结果")
                
        except Exception as e:
            print(f"❌ 股票分析API调用失败: {str(e)}")
            error_message = f"后端服务异常: {str(e)[:100]}"
            
            # 尝试使用模拟数据回退
            try:
                eval_result = get_stock_data(stock_code, use_mock=True)
                is_fallback = True
                error_message = ""
                print("🔄 已使用模拟数据进行回退")
            except Exception as fallback_ex:
                print(f"❌ 模拟数据回退失败: {fallback_ex}")
        
        # ==== 数据处理 ====
        kline_data = eval_result.get("kline_data", {"score": 0, "highlights": [], "recommendation": "中性"})
        sentiment_data = eval_result.get("sentiment_data", {"sentiment_score": 0, "key_events": []})
        assistant_data = eval_result.get("assistant_data", {})
        
        # 更新UI - 先更新静态部分，避免长时间的空白
        # 技术指标展示
        tech_summary = assistant_data.get("tech_summary", "") or kline_data.get("tech_summary", "无技术总结")
        kline_text = format_kline_display(kline_data, tech_summary)
        outputs[0] = kline_text
        
        # 情绪分析展示
        news_summary = assistant_data.get("news_summary", "") or sentiment_data.get("news_summary", "无新闻总结")
        sentiment_text = format_sentiment_display(sentiment_data, news_summary)
        outputs[1] = sentiment_text
        
        # 生成预测图表
        try:
            prediction = generate_prediction_chart(stock_code, assistant_data)
            outputs[2] = prediction.get("chart", None)
            outputs[3] = prediction.get("direction", "未知趋势")
            outputs[4] = prediction.get("change_rate", "0.00%")
        except Exception as e:
            print(f"❌ 图表生成失败: {str(e)}")
            outputs[3] = "图表生成错误"
            outputs[4] = "0.00%"
        
        # 生成投资推荐
        try:
            outputs[5] = generate_investment_recommendation(kline_data, sentiment_data, prediction)
        except Exception as e:
            outputs[5] = "建议生成失败"
            print(f"❌ 投资建议生成失败: {str(e)}")
        
        yield outputs  # 第一次部分更新
        
        # ==== 构建详细建议 ====
        detailed_text = ""
        try:
            # 组合分析过程和详细建议
            analysis_process = assistant_data.get("analysis_process", "无分析过程")
            detailed_recommendation = assistant_data.get("detailed_recommendation", "未获取到详细分析")
            tech_summary = assistant_data.get("tech_summary", "无技术总结")
            news_summary = assistant_data.get("news_summary", "无新闻总结")
            
            if "无分析过程" not in analysis_process:
                detailed_text += f"🧠 分析过程:\n{analysis_process}\n\n"
            
            detailed_text += f"📊 技术总结:\n{tech_summary}\n\n"
            detailed_text += f"📰 新闻总结:\n{news_summary}\n\n"
            detailed_text += f"💎 详细建议:\n{detailed_recommendation}"
            
            if error_message:
                detailed_text += f"\n\n⚠️ 注意: {error_message}"
                
        except Exception as e:
            detailed_text = f"详细建议生成失败: {str(e)}"
            print(f"❌ 详细建议生成失败: {str(e)}")
        
        # 流式输出详细建议（模拟打字效果）
        if detailed_text:
            for i in range(0, len(detailed_text)+1, 5):  # 每次输出5个字符
                outputs[6] = detailed_text[:i]
                yield outputs
                time.sleep(0.05)  # 控制打字速度
        else:
            outputs[6] = "无法生成详细建议，请查看日志"
        
        # 显示反馈区域
        outputs[7] = gr.update(visible=True)
        
        # 保存分析上下文
        outputs[8] = {
            "stock_code": stock_code,
            "prediction": prediction
        }
        
        yield outputs  # 最终更新
        
    except Exception as e:
        print(f"❌ 分析过程发生严重错误: {str(e)}")
        # 简化错误输出
        yield [
            "分析失败",
            "分析失败",
            None, 
            "分析失败", 
            "N/A", 
            "系统错误，请重试或使用模拟模式", 
            f"错误详情: {str(e)[:200]}",
            gr.update(visible=False),
            {}
        ]


# 界面布局
with gr.Blocks(
    title="智能股票分析系统",
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
                info="勾选此选项将使用模拟数据进行分析",
                visible=False  # 隐藏此开关
            )
        with gr.Column(scale=1):
            analyze_btn = gr.Button("🔍 立即分析", variant="primary", size="md")
    
    # 显示当前模式
    mode_status = gr.Markdown(
        value=f"🎭 当前模式: {'模拟数据模式' if USE_MOCK_DATA else '真实数据模式'}",
        visible=False # 隐藏模式状态显示
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
