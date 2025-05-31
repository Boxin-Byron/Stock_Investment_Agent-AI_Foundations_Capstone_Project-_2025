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
        df_ohlcv = pd.read_csv(io.StringIO(request.ohlcv_text))
        required_columns = ['trade_date', 'open', 'high', 'low', 'close', 'vol']
        if not all(col in df_ohlcv.columns for col in required_columns):
            raise ValueError(f"OHLCV CSV 必须包含列: {required_columns}")

        if df_ohlcv.empty:
            raise ValueError("OHLCV 数据不能为空")

        df_ohlcv['trade_date'] = pd.to_datetime(df_ohlcv['trade_date'], format="%Y%m%d")
        df_ohlcv = df_ohlcv.sort_values(by='trade_date').reset_index(drop=True)

        df_ohlcv['ma5'] = df_ohlcv['close'].rolling(window=5, min_periods=1).mean()
        df_ohlcv['ma10'] = df_ohlcv['close'].rolling(window=10, min_periods=1).mean()
        df_ohlcv['ma20'] = df_ohlcv['close'].rolling(window=20, min_periods=1).mean()

        df_ohlcv['volume_change'] = df_ohlcv['vol'].pct_change() * 100
        df_ohlcv['price_change'] = df_ohlcv['close'].pct_change() * 100

        df_ohlcv['volume_change'] = df_ohlcv['volume_change'].replace({np.nan: None})
        df_ohlcv['price_change'] = df_ohlcv['price_change'].replace({np.nan: None})

        df_industry = pd.read_csv(io.StringIO(request.industry_text))
        if len(df_industry) != 1:
            raise ValueError("industry_data CSV 必须只有一行数据")
        industry_data_dict = df_industry.iloc[0].to_dict()

        latest_ohlcv = df_ohlcv.iloc[-1]
        industry_comparison = {}

        for key in ['ma5', 'ma10']:
            bench = industry_data_dict.get(key)
            if bench and not np.isnan(bench):
                industry_comparison[f'{key}_diff_pct'] = ((latest_ohlcv[key] - bench) / bench) * 100
            else:
                industry_comparison[f'{key}_diff_pct'] = None

        bench_vol = industry_data_dict.get('avg_volume')
        if bench_vol and not np.isnan(bench_vol):
            industry_comparison['volume_diff_pct'] = ((latest_ohlcv['vol'] - bench_vol) / bench_vol) * 100
        else:
            industry_comparison['volume_diff_pct'] = None

        for k, v in industry_comparison.items():
            if pd.isna(v):
                industry_comparison[k] = None

        latest_metrics_dict = {
            'date': latest_ohlcv['trade_date'].strftime('%Y-%m-%d'),
            'close': latest_ohlcv['close'],
            'ma5': latest_ohlcv['ma5'],
            'ma10': latest_ohlcv['ma10'],
            'ma20': latest_ohlcv['ma20'],
            'volume': latest_ohlcv['vol'],
            'price_change_pct': latest_ohlcv['price_change'],
            'volume_change_pct': latest_ohlcv['volume_change'],
            'industry_comparison': industry_comparison
        }

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

        processed_data_list = df_ohlcv.replace({np.nan: None}).to_dict(orient='records')
        latest_metrics_string = json.dumps(latest_metrics_dict, ensure_ascii=False, indent=2)

        return {
            "processed_data": processed_data_list,
            "latest_metrics": latest_metrics_string
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"数据处理错误: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码执行遇到意外问题: {str(e)}")
