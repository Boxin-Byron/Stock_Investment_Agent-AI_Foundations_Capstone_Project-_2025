from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import io
import json

app = FastAPI(title="K-Line Analysis API", version="1.0")

class AnalyzeRequest(BaseModel):
    ohlcv_text: str
    industry_text: str

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    try:
        df_daily = pd.read_csv(io.StringIO(request.ohlcv_text))
        required_daily_columns = ['trade_date', 'open', 'high', 'low', 'close', 'vol']
        missing_columns = [col for col in required_daily_columns if col not in df_daily.columns]
        if missing_columns:
            raise ValueError(f"日频 OHLCV 数据缺少必要列: {missing_columns}")

        if df_daily.empty:
            raise ValueError("日频 OHLCV 数据不能为空")

        df_daily['trade_date'] = pd.to_datetime(df_daily['trade_date'], format="%Y%m%d")
        df_daily = df_daily.sort_values(by='trade_date').reset_index(drop=True)

        #计算技术指标_______________________________________________________________________________________________
        # 均线指标
        df_daily['daily_ma5'] = df_daily['close'].rolling(window=5, min_periods=1).mean()
        df_daily['daily_ma10'] = df_daily['close'].rolling(window=10, min_periods=1).mean()
        df_daily['daily_ma20'] = df_daily['close'].rolling(window=20, min_periods=1).mean()

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

        df_industry = pd.read_csv(io.StringIO(request.industry_text))
        if len(df_industry) != 1:
            raise ValueError("industry_data CSV 必须只有一行数据")
        industry_data_dict = df_industry.iloc[0].to_dict()

        latest_ohlcv = df_daily.iloc[-1]
        industry_comparison = {}

        # 1. 均线与成交量比较
        for key in ['daily_ma5', 'daily_ma10', 'daily_rsi6']:
            bench = industry_data_dict.get(key)
            if bench and not np.isnan(bench):
                industry_comparison[f'{key}_diff_pct'] = ((latest_ohlcv[key] - bench) / bench) * 100
            else:
                industry_comparison[f'{key}_diff_pct'] = None

        bench_vol = industry_data_dict.get('avg_volume')
        if bench_vol and not np.isnan(bench_vol):
            industry_comparison['daily_volume_diff_pct'] = ((latest_ohlcv['vol'] - bench_vol) / bench_vol) * 100
        else:
            industry_comparison['daily_volume_diff_pct'] = None

        # 2. 技术信号识别
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
        macd = latest_ohlcv.get('daily_macd')
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

        # 3. 最新指标字典整合
        latest_metrics_dict = {
            'date': latest_ohlcv['trade_date'].strftime('%Y-%m-%d'),
            'close': latest_ohlcv['close'],
            'volume': latest_ohlcv['vol'],
            'price_change_pct': latest_ohlcv['daily_price_change_pct'],
            'volume_change_pct': latest_ohlcv['daily_volume_change_pct'],
            'industry_comparison': industry_comparison,
            'technical_signals': signal_analysis,
        }

        # 附加指标值（如均线、RSI、MACD 等）加入 latest_metrics_dict
        for col in ['daily_ma5', 'daily_ma10', 'daily_ma20', 'daily_rsi6', 'daily_macd', 'daily_macd_diff', 'daily_macd_dea', 'daily_k', 'daily_d', 'daily_j']:
            val = latest_ohlcv.get(col)
            latest_metrics_dict[col] = None if pd.isna(val) else float(val)

        # 数据清洗
        for k, v in latest_metrics_dict.items():
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    if pd.isna(sub_v):
                        v[sub_k] = None
            elif pd.isna(v):
                latest_metrics_dict[k] = None
            elif isinstance(v, (np.integer)):
                latest_metrics_dict[k] = int(v)
            elif isinstance(v, (np.floating, np.float64)):
                latest_metrics_dict[k] = float(v)

        # processed_data_list = df_daily.replace({np.nan: None}).to_dict(orient='records')
        latest_metrics_string = json.dumps(latest_metrics_dict, ensure_ascii=False, indent=2)

        # return {
        #     "processed_data": processed_data_list,
        #     "latest_metrics": latest_metrics_string
        # }
        return {"latest_metrics": latest_metrics_string}


    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"数据处理错误: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码执行遇到意外问题: {str(e)}")
