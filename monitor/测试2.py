import re

# 原始文本
text = '''
### 技术面总结 - 当前趋势阶段：震荡整理 - 多项关键指标分析： - RSI中性(44.65), MACD无明显信号, KDJ中性 - 布林带显示未突破(中轨1463.52, 上轨1546.29, 下轨1380.76) - ATR14显示高波动(24.10) - CCI中 性(-69.53)，Bias6和Bias12均处于正常范围 - 存在高波动风险，但无明显的超买超卖共振信号 ### 新闻情绪总结 - 总体情绪倾向及得分：中性偏微幅正面(0.09) - 关键事件与潜在影响路径： - 公司新闻和财务报告更新 - 北上资金交易动向 - 股价走势和市场表现 ### 综合判断与投资建议 - 当前建议：控制仓 位，可考虑观望或使用对冲策略 - 未来一周趋势方向：预计维持震荡格局 - 主要逻辑证据： - 日线技术指标整体中性 - 情绪指标中性无催化剂 - 高波动信号提示需警惕短期波动 - 潜在风险提示： - 高波动下存在短期价格波动风险 - 技术指标出现滞后性
'''

# 使用正则表达式提取三部分
tech_summary = re.search(r'### 技术面总结(.*?)### 新闻情绪总结', text, re.DOTALL)
sentiment_summary = re.search(r'### 新闻情绪总结(.*?)### 综合判断与投资建议', text, re.DOTALL)
investment_suggestion = re.search(r'### 综合判断与投资建议(.*)', text, re.DOTALL)

# 提取结果
if tech_summary and sentiment_summary and investment_suggestion:
    tech_summary = tech_summary.group(1).strip()
    sentiment_summary = sentiment_summary.group(1).strip()
    investment_suggestion = investment_suggestion.group(1).strip()
    
    print("### 1. 技术面总结")
    print(tech_summary)
    
    print("\n### 2. 新闻情绪总结")
    print(sentiment_summary)
    
    print("\n### 3. 综合判断与投资建议")
    print(investment_suggestion)
else:
    print("未能成功提取全部内容")
