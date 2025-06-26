import re

# 原始文本
text = '### 技术面总结\n- 当前趋势阶段：震荡阶段\n- 多项关键指标分析（MACD、KDJ、RSI、布林带、ATR等）: \n  - RSI: 44.65 (中性)\n  - MACD: -0.13 (无明显信号)\n  - KDJ: K=40.45, D=32.35, J=56.65 (中性)\n  - 布林带: 价格位于中轨1463.52和下轨1380.76之间(未突破)\n  - ATR: 24.10 (高波动)\n- 是否存在技术共振信号: 无多个一致信号\n\n### 新闻情绪总结\n- 总体情绪倾向及得分: 中性(0.15)\n- 关键事件与潜在影响路径: 贵州茅台与京东及阿里就电高营策略交流，北上资金买卖情况及机构博弈动态\n\n### 综合判断与投资建议\n- 当前建议: 控制仓位, 可通过其他方式对冲风险\n- 对未来一周的趋势方向及可能变动幅度估计: 震荡\n- 支持该判断的主要逻辑证据: 技术指标整体呈中性,布林带处于正常范围，成交量正常,新闻情绪中性\n- 潜在风险提示: 情绪反转可能导致价格剧烈波动,技术指标可能出现假信号'

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
