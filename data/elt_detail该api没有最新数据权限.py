from jqdatasdk import get_price, get_query_count, logout
import pandas as pd
from datetime import datetime

def get_kline_jq(stock_code, days=1):
    # JoinQuant 格式：600519.XSHG, 000001.XSHE
    if stock_code.startswith('6'):
        jq_code = stock_code + ".XSHG"
    else:
        jq_code = stock_code + ".XSHE"

    end_date = datetime.today()
    start_date = pd.bdate_range(end=end_date, periods=days+1, freq='C')[0]  # 多取一天保证有数据
    start_date_str = start_date.strftime('%Y-%m-%d 09:00:00')
    end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

    data = get_price(
        jq_code,
        start_date=start_date_str,
        end_date=end_date_str,
        fq='post',
        frequency='minute',
        fields=[
            'open', 'close', 'low', 'high',  'money', 'avg', 'pre_close'
        ],
        round=False
    )

    df = pd.DataFrame(data)
    df.rename(columns={"money": "vol"}, inplace=True)
    df['trade_date'] = df['index'].dt.strftime("%Y%m%d")
    df = df[['trade_date', 'open', 'high', 'low', 'close', 'vol']]

    output_path = f"data/detail_{stock_code}.csv"
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✅ 已保存：{output_path}")

# 示例调用
if __name__ == "__main__":
    from jqdatasdk import auth
    auth('18192108075', 'Zbx08170715')
    print(get_query_count())
    code = input("请输入股票代码（如600519）：")
    days = input("请输入查询最近几个交易日（默认1）：")
    days = int(days) if days.strip() else 1
    get_kline_jq(code, days)
    logout()
