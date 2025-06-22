import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Optional

# 从环境变量获取配置
MAIRUI_LICENCE = os.getenv('MAIRUI_LICENCE', "9914AFE5-493E-41DD-9C02-4F7145666C13")  # 默认值用于本地开发

def format_mairui_code(code: str):
    return code + ".SH" if code.startswith("6") else code + ".SZ"


def get_last_n_trading_days_precise(end_datetime: datetime, n=5, today: Optional[datetime] = None) -> tuple[str, str]:
    """
    获取精确的过去 n 个交易日的起止日期字符串，时间段为：
    start = 第一个交易日的09:30:00
    end   = 若 today 为 None 则为当前时间；否则为 today 的 15:00:00
    """    # 使用 jqdata 获取交易日历
    from jqdatasdk import auth, get_trade_days
    # 从环境变量获取聚宽账号密码
    JQ_USERNAME = os.getenv('JQ_USERNAME', '18192108075')  # 默认值用于本地开发
    JQ_PASSWORD = os.getenv('JQ_PASSWORD', 'Zbx08170715')  # 默认值用于本地开发
    auth(JQ_USERNAME, JQ_PASSWORD)

    if end_datetime is None:
        end_datetime = datetime.today()
    end_dt_str = end_datetime.strftime('%Y-%m-%d')
    trade_days = get_trade_days(end_date=end_dt_str, count=n)
    trade_dates = [pd.to_datetime(d).strftime('%Y%m%d') for d in trade_days]

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

def get_kline_mairui_5min(stock_code: str, today: Optional[datetime] = None) -> pd.DataFrame:
    ts_code = format_mairui_code(stock_code)
    end_dt = today or datetime.now()
    start_time, end_time = get_last_n_trading_days_precise(end_dt, n=5, today=today)
    print(f"📅 获取数据时间范围：{start_time} - {end_time}"
          f"（股票代码：{stock_code}）")
    
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

        # 兼容返回为 dict 或 list 的情况
        if isinstance(json_data, dict):
            if json_data.get("code") != 200:
                print(f"❌ 接口错误：{json_data.get('msg')}")
                raise ValueError(f"接口错误：{json_data.get('msg')}")
            data = json_data.get('data', [])
        elif isinstance(json_data, list):
            data = json_data
        else:
            print("❌ 未知的返回格式")
            raise ValueError("未知的返回格式")

        df = pd.DataFrame(data)

        df.rename(columns={
            "t": "trade_time", "o": "open", "h": "high",
            "l": "low", "c": "close", "v": "volume"
        }, inplace=True)
        df['trade_time'] = pd.to_datetime(df['trade_time'])
        df = df[['trade_time', 'open', 'high', 'low', 'close', 'volume']]
        df.sort_values('trade_time', inplace=True)
        return df
        
    except Exception as e:
        print(f"❗ 请求失败：{e}")
        return pd.DataFrame()

# 示例调用
if __name__ == "__main__":
    stock_code = input("请输入A股股票代码（如600519）：").strip()
    
    # today = None 表示实时
    # today = datetime(2024, 5, 22, 15, 0, 0)  # 回测用
    today = None

    df = get_kline_mairui_5min(stock_code, today=None)
    end_dt = today or datetime.now()
    suffix = end_dt.strftime('%Y%m%d')
    output_path = f"./temp/intraday_{stock_code}_5min.csv"
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✅ 已保存至：{output_path}")