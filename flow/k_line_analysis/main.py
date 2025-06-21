from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import io
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# 确保能够导入当前目录的模块
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

# 直接从本地导入模块
from etl import get_kline_csv
from elt_intraday import get_kline_mairui_5min

app = FastAPI(title="K-Line Analysis API", version="1.0")

class AnalyzeRequest(BaseModel):
    stock_code: str

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

def get_stock_data(stock_code: str, today: Optional[datetime] = None):
    """
    获取股票的日K线和分钟K线数据
    
    Args:
        stock_code: 股票代码，如600519
        today: 可选的日期参数，用于回测
        
    Returns:
        tuple: (日K线文件路径, 分钟K线文件路径)
    """
    print(f"🔄 开始获取股票 {stock_code} 的数据...")
    
    # 确保temp目录存在
    os.makedirs("temp", exist_ok=True)
    
    # 获取日K线数据
    print("📊 获取日K线数据...")
    df1 = get_kline_csv(stock_code, today)
    
    # 获取5分钟K线数据
    print("📈 获取5分钟K线数据...")
    df2 = get_kline_mairui_5min(stock_code, today)
    if df1.empty and df2.empty:
        raise ValueError(f"获取股票 {stock_code} 的数据失败，请检查股票代码或网络连接。")

    return df1, df2

def analyze_daily_metrics(df_daily: pd.DataFrame) -> dict:
    """
    分析日K线数据，计算最新指标值
    
    Args:
        df_daily: 日K线数据的DataFrame
        
    Returns:
        dict: 最新指标值字典
    """
    if df_daily.empty:
        return {
            'date': None,
            'close': None,
            'volume': None,
            'price_change_pct': None,
            'volume_change_pct': None,
            'technical_signals': {},
            'daily_technical_indicators': {
                'rsi': None,
                'macd_diff': None,
                'macd_dea': None,
                'macd': None,
                'k': None,
                'd': None,
                'j': None,
                'boll_mid': None,
                'boll_upper': None,
                'boll_lower': None,
                'cci': None,
                'atr14': None,
                'bias6': None,
                'bias12': None
            }
        }
    df_daily['trade_date'] = pd.to_datetime(df_daily['trade_date'], format="%Y%m%d")
    df_daily = df_daily.sort_values(by='trade_date').reset_index(drop=True)

    #计算技术指标_______________________________________________________________________________________________

    # 成交量与价格变化率
    df_daily['daily_volume_change_pct'] = df_daily['vol'].pct_change() * 100
    df_daily['daily_price_change_pct'] = df_daily['close'].pct_change() * 100

    # -------------------- 技术指标扩展 --------------------

    # MACD
    ema12 = df_daily['close'].ewm(span=12, adjust=False).mean()
    ema26 = df_daily['close'].ewm(span=26, adjust=False).mean()
    df_daily['daily_macd_diff'] = ema12 - ema26
    df_daily['daily_macd_dea'] = df_daily['daily_macd_diff'].ewm(span=9, adjust=False).mean()
    df_daily['daily_macd'] = 2 * (df_daily['daily_macd_diff'] - df_daily['daily_macd_dea'])

    # KDJ
    low_n = df_daily['low'].rolling(window=9, min_periods=1).min()
    high_n = df_daily['high'].rolling(window=9, min_periods=1).max()
    rsv = (df_daily['close'] - low_n) / (high_n - low_n) * 100
    df_daily['daily_k'] = rsv.ewm(com=2).mean()
    df_daily['daily_d'] = df_daily['daily_k'].ewm(com=2).mean()
    df_daily['daily_j'] = 3 * df_daily['daily_k'] - 2 * df_daily['daily_d']

    # RSI
    def calc_rsi(series, period):
        delta = series.diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).rolling(window=period).mean()
        avg_loss = pd.Series(loss).rolling(window=period).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        return 100 - (100 / (1 + rs))

    df_daily['daily_rsi6'] = calc_rsi(df_daily['close'], 6)
    df_daily['daily_rsi12'] = calc_rsi(df_daily['close'], 12)
    df_daily['daily_rsi24'] = calc_rsi(df_daily['close'], 24)

    # BOLL（布林带）
    ma20 = df_daily['close'].rolling(window=20).mean()
    std20 = df_daily['close'].rolling(window=20).std()
    df_daily['daily_boll_mid'] = ma20
    df_daily['daily_boll_upper'] = ma20 + 2 * std20
    df_daily['daily_boll_lower'] = ma20 - 2 * std20

    # BIAS（乖离率）
    df_daily['daily_bias6'] = (df_daily['close'] - df_daily['close'].rolling(window=6).mean()) / df_daily['close'].rolling(window=6).mean() * 100
    df_daily['daily_bias12'] = (df_daily['close'] - df_daily['close'].rolling(window=12).mean()) / df_daily['close'].rolling(window=12).mean() * 100

    # CCI（顺势指标）
    tp = (df_daily['high'] + df_daily['low'] + df_daily['close']) / 3
    ma_tp = tp.rolling(window=14).mean()
    md = tp.rolling(window=14).apply(lambda x: np.mean(np.abs(x - x.mean())))
    df_daily['daily_cci'] = (tp - ma_tp) / (0.015 * md)

    # ATR（平均真实波幅）
    high_low = df_daily['high'] - df_daily['low']
    high_close = pd.Series(np.abs(df_daily['high'] - df_daily['close'].shift()), index=df_daily.index)
    low_close = pd.Series(np.abs(df_daily['low'] - df_daily['close'].shift()), index=df_daily.index)
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df_daily['daily_atr14'] = tr.rolling(window=14).mean()

    # 清理 NaN -> None 
    df_daily = df_daily.replace({np.nan: None})
    
    #____________________________________________________________________________________________

    latest_ohlcv = df_daily.iloc[-1]

    # 1. 技术信号识别
    signal_analysis = {}

    # RSI 信号：超买 >70，超卖 <30
    rsi = latest_ohlcv.get('daily_rsi6')
    if rsi is not None:
        if rsi > 70:
            signal_analysis['rsi_signal'] = '超买'
        elif rsi < 30:
            signal_analysis['rsi_signal'] = '超卖'
        else:
            signal_analysis['rsi_signal'] = '中性'

    # MACD 金叉死叉判断
    macd_diff = latest_ohlcv.get('daily_macd_diff')
    macd_dea = latest_ohlcv.get('daily_macd_dea')
    if macd_diff is not None and macd_dea is not None:
        prev = df_daily.iloc[-2]
        prev_diff = prev.get('daily_macd_diff')
        prev_dea = prev.get('daily_macd_dea')
        if prev_diff is not None and prev_dea is not None:
            if prev_diff < prev_dea and macd_diff > macd_dea:
                signal_analysis['macd_signal'] = '金叉'
            elif prev_diff > prev_dea and macd_diff < macd_dea:
                signal_analysis['macd_signal'] = '死叉'
            else:
                signal_analysis['macd_signal'] = '无明显信号'

    # KDJ 判断：J 值极端代表短期拐点
    j = latest_ohlcv.get('daily_j')
    if j is not None:
        if j > 100:
            signal_analysis['kdj_signal'] = '超买拐点'
        elif j < 0:
            signal_analysis['kdj_signal'] = '超卖拐点'
        else:
            signal_analysis['kdj_signal'] = '中性'


    # BOLL 布林带突破
    boll_upper = latest_ohlcv.get('daily_boll_upper')
    boll_lower = latest_ohlcv.get('daily_boll_lower')
    if boll_upper is not None and boll_lower is not None:
        if latest_ohlcv['close'] > boll_upper:
            signal_analysis['boll_signal'] = '突破上轨'
        elif latest_ohlcv['close'] < boll_lower:
            signal_analysis['boll_signal'] = '突破下轨'
        else:
            signal_analysis['boll_signal'] = '未突破'
    
    # BIAS 乖离率信号
    bias6 = latest_ohlcv.get('daily_bias6')
    bias12 = latest_ohlcv.get('daily_bias12')
    if bias6 is not None and bias12 is not None:
        if bias6 > 10 or bias12 > 10:
            signal_analysis['bias_signal'] = '偏离上轨'
        elif bias6 < -10 or bias12 < -10:
            signal_analysis['bias_signal'] = '偏离下轨'
        else:
            signal_analysis['bias_signal'] = '正常范围'

    # CCI 信号：超买 >100，超卖 <-100
    cci = latest_ohlcv.get('daily_cci')
    if cci is not None:
        if cci > 100:
            signal_analysis['cci_signal'] = '超买'
        elif cci < -100:
            signal_analysis['cci_signal'] = '超卖'
        else:
            signal_analysis['cci_signal'] = '中性'
    
    # ATR 波动率信号：高波动 >2，低波动 <0.5
    atr14 = latest_ohlcv.get('daily_atr14')
    if atr14 is not None:
        if atr14 > 2:
            signal_analysis['atr_signal'] = '高波动'
        elif atr14 < 0.5:
            signal_analysis['atr_signal'] = '低波动'
        else:
            signal_analysis['atr_signal'] = '正常波动'
    
    # 2. 构建最新指标字典    
    latest_metrics_dict = {
        'date': latest_ohlcv['trade_date'].strftime('%Y-%m-%d'),
        'close': latest_ohlcv['close'],
        'volume': latest_ohlcv['vol'],
        'price_change_pct': latest_ohlcv['daily_price_change_pct'],
        'volume_change_pct': latest_ohlcv['daily_volume_change_pct'],
        'technical_signals': signal_analysis,
        'daily_technical_indicators': {'rsi': latest_ohlcv.get('daily_rsi6'),
                                'macd_diff': latest_ohlcv.get('daily_macd_diff'),
                                'macd_dea': latest_ohlcv.get('daily_macd_dea'),
                                'macd': latest_ohlcv.get('daily_macd'),
                                'k': latest_ohlcv.get('daily_k'),
                                'd': latest_ohlcv.get('daily_d'),
                                'j': latest_ohlcv.get('daily_j'),
                                'boll_mid': latest_ohlcv.get('daily_boll_mid'),
                                'boll_upper': latest_ohlcv.get('daily_boll_upper'),
                                'boll_lower': latest_ohlcv.get('daily_boll_lower'),
                                'cci': latest_ohlcv.get('daily_cci'),
                                'atr14': latest_ohlcv.get('daily_atr14'),
                                'bias6': latest_ohlcv.get('daily_bias6'),
                                'bias12': latest_ohlcv.get('daily_bias12')}
    }
    return latest_metrics_dict

def analyze_intraday_metrics(df_intraday: pd.DataFrame) -> dict:
    """
    分析分钟K线数据，计算最新指标值
    
    Args:
        df_intraday: 分钟K线数据的DataFrame
        
    Returns:
        dict: 最新指标值字典
    """
    if df_intraday.empty:
        return {
            'price_change_pct': None,
            'volume_change_pct': None,
            'intraday_technical_indicators': {
                'rsi_30min': None,
                'rsi_60min': None,
                'rsi_120min': None,
                'macd_diff': None,
                'macd_dea': None,
                'macd': None,
                'k': None,
                'd': None,
                'j': None,
                'boll_120min_mid': None,
                'boll_120min_upper': None,
                'boll_120min_lower': None,
                'cci': None,
                'atr_120min': None
            }
        }
    df_intraday['trade_time'] = pd.to_datetime(df_intraday['trade_time'])
    df_intraday = df_intraday.sort_values(by='trade_time').reset_index(drop=True)

    # 计算技术指标
    df_intraday['intraday_volume_change_pct'] = df_intraday['volume'].pct_change() * 100
    df_intraday['intraday_price_change_pct'] = df_intraday['close'].pct_change() * 100

    # MACD
    ema12 = df_intraday['close'].ewm(span=12, adjust=False).mean()
    ema26 = df_intraday['close'].ewm(span=26, adjust=False).mean()
    df_intraday['intraday_macd_diff'] = ema12 - ema26
    df_intraday['intraday_macd_dea'] = df_intraday['intraday_macd_diff'].ewm(span=9, adjust=False).mean()
    df_intraday['intraday_macd'] = 2 * (df_intraday['intraday_macd_diff'] - df_intraday['intraday_macd_dea'])

    # KDJ
    low_n = df_intraday['low'].rolling(window=9, min_periods=1).min()
    high_n = df_intraday['high'].rolling(window=9, min_periods=1).max()
    rsv = (df_intraday['close'] - low_n) / (high_n - low_n) * 100
    df_intraday['intraday_k'] = rsv.ewm(com=2).mean()
    df_intraday['intraday_d'] = df_intraday['intraday_k'].ewm(com=2).mean()
    df_intraday['intraday_j'] = 3 * df_intraday['intraday_k'] - 2 * df_intraday['intraday_d']

    # RSI
    def calc_rsi(series, period):
        delta = series.diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).rolling(window=period).mean()
        avg_loss = pd.Series(loss).rolling(window=period).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        return 100 - (100 / (1 + rs))

    df_intraday['intraday_rsi_30min'] = calc_rsi(df_intraday['close'], 6)
    df_intraday['intraday_rsi_60min'] = calc_rsi(df_intraday['close'], 12)
    df_intraday['intraday_rsi_120min'] = calc_rsi(df_intraday['close'], 24)

    # BOLL（布林带）
    ma24 = df_intraday['close'].rolling(window=24).mean()
    std24 = df_intraday['close'].rolling(window=24).std()
    df_intraday['intraday_boll_120min_mid'] = ma24
    df_intraday['intraday_boll_120min_upper'] = ma24 + 2 * std24
    df_intraday['intraday_boll_120min_lower'] = ma24 - 2 * std24

    # CCI（顺势指标）
    tp = (df_intraday['high'] + df_intraday['low'] + df_intraday['close']) / 3
    ma_tp = tp.rolling(window=14).mean()
    md = tp.rolling(window=14).apply(lambda x: np.mean(np.abs(x - x.mean())))
    df_intraday['intraday_cci'] = (tp - ma_tp) / (0.015 * md)

    # ATR（平均真实波幅）
    high_low = df_intraday['high'] - df_intraday['low']
    high_close = pd.Series(np.abs(df_intraday['high'] - df_intraday['close'].shift()), index=df_intraday.index)
    low_close = pd.Series(np.abs(df_intraday['low'] - df_intraday['close'].shift()), index=df_intraday.index)
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df_intraday['intraday_atr_120min'] = tr.rolling(window=24).mean()

    # 清理 NaN -> None 
    df_intraday = df_intraday.replace({np.nan: None})
    latest_intraday = df_intraday.iloc[-1]
    
    latest_metrics_dict = {
        'price_change_pct': latest_intraday['intraday_price_change_pct'],
        'volume_change_pct': latest_intraday['intraday_volume_change_pct'],
        'intraday_technical_indicators': {
            'rsi_30min': latest_intraday.get('intraday_rsi_30min'),
            'rsi_60min': latest_intraday.get('intraday_rsi_60min'),
            'rsi_120min': latest_intraday.get('intraday_rsi_120min'),
            'macd_diff': latest_intraday.get('intraday_macd_diff'),
            'macd_dea': latest_intraday.get('intraday_macd_dea'),
            'macd': latest_intraday.get('intraday_macd'),
            'k': latest_intraday.get('intraday_k'),
            'd': latest_intraday.get('intraday_d'),
            'j': latest_intraday.get('intraday_j'),
            'boll_120min_mid': latest_intraday.get('intraday_boll_120min_mid'),
            'boll_120min_upper': latest_intraday.get('intraday_boll_120min_upper'),
            'boll_120min_lower': latest_intraday.get('intraday_boll_120min_lower'),
            'cci': latest_intraday.get('intraday_cci'),
            'atr_120min': latest_intraday.get('intraday_atr_120min')
        }
    }
    return latest_metrics_dict








@app.post("/analyze")
def analyze(request: AnalyzeRequest, today: Optional[datetime] = None):
    try:
        # 使用集成的数据获取函数
        df_daily, df_intraday = get_stock_data(request.stock_code, today)
        if df_daily.empty and df_intraday.empty:
            raise ValueError(f"获取股票 {request.stock_code} 的数据失败，请检查股票代码或网络连接。")
        # 分析日K线数据
        latest_metrics_dict = analyze_daily_metrics(df_daily)
        # 分析分钟K线数据
        latest_intraday_metrics_dict = analyze_intraday_metrics(df_intraday)
        # 合并日K线和分钟K线的指标
        latest_metrics_dict.update(latest_intraday_metrics_dict)
        # 添加股票代码
        latest_metrics_dict['stock_code'] = request.stock_code
        # 添加当前时间戳
        today = today or datetime.now()
        latest_metrics_dict['timestamp'] = today.strftime('%Y-%m-%d %H:%M:%S')


        latest_metrics_string = json.dumps(latest_metrics_dict, ensure_ascii=False, indent=2)
        return {"latest_metrics": latest_metrics_string}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码执行遇到意外问题: {str(e)}")


# 命令行直接执行模式
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="股票K线数据获取与分析")
    parser.add_argument("--code", type=str, help="股票代码，如600519")
    parser.add_argument("--backtest", type=str, help="回测日期，格式YYYY-MM-DD，如2025-06-20")
    parser.add_argument("--mode", choices=['data', 'api'], default='data',
                       help="模式：data=只获取数据，api=启动API服务")
    
    args = parser.parse_args()
    
    # API模式：启动FastAPI服务
    if args.mode == 'api':
        import uvicorn
        print("🚀 正在启动K线分析API服务")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    
    # 数据获取模式
    elif args.mode == 'data':
        # 如果命令行没有提供参数，交互式输入
        if not args.code:
            args.code = input("请输入股票代码（如600519）：").strip()
        
        # 处理回测日期
        today = None
        if args.backtest:
            try:
                today = datetime.strptime(args.backtest, "%Y-%m-%d")
                print(f"🕰️ 回测模式: {today.strftime('%Y-%m-%d')}")
            except ValueError:
                print("⚠️ 回测日期格式错误，使用当前日期")
        
        # 只获取数据
        df_daily, df_intraday = get_stock_data(args.code, today)
        output_path1 = f"./temp/kline_{args.code}.csv"
        os.makedirs("temp", exist_ok=True)
        df_daily.to_csv(output_path1, index=False)
        print(f"成功保存：{output_path1}")
        
        end_dt = today or datetime.now()
        suffix = end_dt.strftime('%Y%m%d')
        output_path = f"./temp/intraday_{args.code}_{suffix}_5min.csv"
        df_intraday.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ 已保存至：{output_path}")
