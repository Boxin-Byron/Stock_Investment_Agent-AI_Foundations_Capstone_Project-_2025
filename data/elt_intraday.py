import requests
import pandas as pd
import os
from datetime import datetime, timedelta
import tushare as ts
from typing import Optional

# 配置
MAIRUI_LICENCE = "9914AFE5-493E-41DD-9C02-4F7145666C13"

def format_mairui_code(code: str):
    return code + ".SH" if code.startswith("6") else code + ".SZ"

from akshare import tool_trade_date_hist_sina

def get_last_n_trading_days_precise(end_datetime: datetime, n=5, today: Optional[datetime] = None) -> tuple[str, str]:
    """
    获取精确的过去 n 个交易日的起止日期字符串，时间段为：
    start = 第一个交易日的09:30:00
    end   = 若 today 为 None 则为当前时间；否则为 today 的 15:00:00
    """
    trade_dates = tool_trade_date_hist_sina()
    # 过滤掉不是日期格式的元素（如表头等）
    trade_dates = [d for d in trade_dates if isinstance(d, str) and len(d) == 10 and d[4] == '-' and d[7] == '-']
    trade_dates = [d for d in trade_dates if datetime.strptime(d, '%Y-%m-%d') <= end_datetime]
    trade_dates = [d.replace('-', '') for d in trade_dates]

    if len(trade_dates) < n:
        raise ValueError("交易日数量不足")

    start_day = trade_dates[-n]
    end_day = trade_dates[-1]

    start_time = f"{start_day}093000"
    if today is None:
        end_time = datetime.now().strftime('%Y%m%d%H%M%S')
    else:
        end_time = f"{end_day}150000"

    return start_time, end_time

def get_kline_mairui_5min(stock_code: str, today: Optional[datetime] = None):
    ts_code = format_mairui_code(stock_code)
    end_dt = today or datetime.now()
    start_time, end_time = get_last_n_trading_days_precise(end_dt, n=5, today=today)

    url = (
        f"https://api.mairuiapi.com/hsstock/history/"
        f"{ts_code}/5/n/{MAIRUI_LICENCE}"
        f"?st={start_time}&et={end_time}"
    )
    print(f"📡 请求数据：{url}")

    try:
        response = requests.get(url)
        response.raise_for_status()
        json_data = response.json()

        if json_data.get("code") != 200:
            print(f"❌ 接口错误：{json_data.get('msg')}")
            return

        df = pd.DataFrame(json_data['data'])

        df.rename(columns={
            "t": "trade_time", "o": "open", "h": "high",
            "l": "low", "c": "close", "v": "volume"
        }, inplace=True)
        df['trade_time'] = pd.to_datetime(df['trade_time'])
        df = df[['trade_time', 'open', 'high', 'low', 'close', 'volume']]
        df.sort_values('trade_time', inplace=True)

        os.makedirs("data", exist_ok=True)
        suffix = end_dt.strftime('%Y%m%d')
        output_path = f"./temp/intraday_{stock_code}_{suffix}_5min.csv"
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ 已保存至：{output_path}")
    except Exception as e:
        print(f"❗ 请求失败：{e}")

# 示例调用
if __name__ == "__main__":
    stock_code = input("请输入A股股票代码（如600519）：").strip()
    
    # today = None 表示实时
    # today = datetime(2024, 5, 22, 15, 0, 0)  # 回测用
    today = None

    get_kline_mairui_5min(stock_code, today=None)