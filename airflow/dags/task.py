from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from sqlalchemy import create_engine
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
import os

db_path = '/opt/airflow/dags/crypto_data.db'
engine = create_engine(f'sqlite:///{db_path}')
tickers = ["BTC-USD", "ETH-USD", "ADA-USD", "BNB-USD", "XRP-USD",
           "LTC-USD", "BCH-USD", "EOS-USD", "TRX-USD", "USDT-USD"]
short_names = sorted([t.replace("-USD", "") for t in tickers])

def save_raw_data():
    today = datetime.today()
    yesterday_2 = today - timedelta(days=2)
    
    data = yf.download(tickers, start=yesterday_2, end=today, interval='1d')

    df_close = data['Close'].rename(columns=lambda x: x[:-4])
    df_volume = data['Volume'].rename(columns=lambda x: x[:-4])

    df_raw = df_close.copy()
    for crypto in df_close.columns:
        df_raw[f'{crypto}_Volume'] = df_volume[crypto]

    df_raw = df_raw.reset_index()
    df_raw['Date'] = pd.to_datetime(df_raw['Date']).dt.date  

    latest_date = df_raw['Date'].max()
    query = f"SELECT 1 FROM crypto_raw WHERE Date = '{latest_date}' LIMIT 1"
    exists = pd.read_sql(query, engine)

    if not exists.empty:
        print(f"Dữ liệu ngày {latest_date} đã tồn tại trong database, bỏ qua.")
        return

    df_raw.to_sql('crypto_raw', engine, if_exists='append', index=False)
    print(f"Đã lưu dữ liệu thô (close, volume) đến ngày {df_raw['Date'].max()} vào bảng crypto_raw.")

def calculate_and_save_features():
    df_raw = pd.read_sql('SELECT * FROM crypto_raw', engine, parse_dates=['Date'])
    df_raw = df_raw.set_index('Date').sort_index()

    df_feat = pd.DataFrame(index=df_raw.index)

    for crypto in short_names:
        close = df_raw[crypto]
        volume = df_raw[f'{crypto}_Volume']

        if close.index.duplicated().any():
            close = close[~close.index.duplicated(keep='first')]

        macd = ta.macd(close)['MACD_12_26_9']
        rsi = ta.rsi(close)
        bbands = ta.bbands(close)
        bb_upper = bbands['BBU_5_2.0']
        bb_lower = bbands['BBL_5_2.0']
        volatility = close.pct_change().rolling(20).std() * np.sqrt(252)

        df_feat[f'{crypto}_MACD'] = macd
        df_feat[f'{crypto}_RSI'] = rsi
        df_feat[f'{crypto}_BB_upper'] = bb_upper
        df_feat[f'{crypto}_BB_lower'] = bb_lower
        df_feat[f'{crypto}_Volume'] = volume
        df_feat[f'{crypto}_Volatility'] = volatility

    df_feat.dropna(inplace=True)

    scaler = MinMaxScaler()
    df_feat[df_feat.columns] = scaler.fit_transform(df_feat)

    df_feat = df_feat.reset_index()
    df_merged = pd.merge(df_raw, df_feat, on='Date', how='inner')

    df_merged.to_sql('crypto_features', engine, if_exists='replace', index=False)
    print(f"Đã lưu dữ liệu tính toán các chỉ báo kỹ thuật vào bảng crypto_features.")

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 4, 25),
    'retries': 0,
}

with DAG(
    'update_crypto_latest',
    default_args=default_args,
    schedule_interval='@daily', 
    catchup=False,
) as dag:

    task_crawl_raw = PythonOperator(
        task_id='crawl_raw_crypto_data',
        python_callable=save_raw_data,
    )

    task_calculate_and_save_features = PythonOperator(
        task_id='calculate_and_save_features',
        python_callable=calculate_and_save_features,
    )


    task_crawl_raw >> task_calculate_and_save_features
