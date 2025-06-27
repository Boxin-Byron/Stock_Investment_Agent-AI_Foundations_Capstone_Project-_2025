import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import os
from typing import Optional

# 从环境变量获取 Tushare Token
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api()

def format_ts_code(code: str):
    """将 A 股代码转为 Tushare ts_code 格式"""
    if code.startswith("6"):
        return code + ".SH"
    else:
        return code + ".SZ"

def get_kline_csv(stock_code: str, today: Optional[datetime] = None) -> pd.DataFrame:
    """
    Fetches recent daily K-line (candlestick) data for a given stock code using Tushare.
    Args:
        stock_code (str): The stock code to fetch data for.
        today (Optional[datetime], optional): The end date for data retrieval. Defaults to current date if not provided.
    Returns:
        pandas.DataFrame: DataFrame containing the K-line data for the specified stock, or None if data retrieval fails.
    Raises:
        Prints an error message if data retrieval fails.
    """
    ts_code = format_ts_code(stock_code)

    # 拉取最近 100 个自然日，Tushare 会自动返回其中最多 50 个交易日
    end_date = today if today else datetime.now()
    start_date = end_date - timedelta(days=100)
    start = start_date.strftime("%Y%m%d")
    end = end_date.strftime("%Y%m%d")

    try:
        df = pro.daily(ts_code=ts_code, start_date=start, end_date=end)
        # df = df[['trade_date', 'open', 'high', 'low', 'close', 'vol']]
        # df.sort_values('trade_date', inplace=True)
        return df
    except Exception as e:
        print(f"数据获取失败：{e}")
        return pd.DataFrame()

if __name__ == '__main__':
    stock_code = input("请输入股票代码（如600519）：")
    # today = datetime(2024, 5, 22)  # 指定某一天用于回测
    df = get_kline_csv(stock_code, today=None)
    output_path = f"./temp/kline_{stock_code}.csv"
    os.makedirs("temp", exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"成功保存：{output_path}")
