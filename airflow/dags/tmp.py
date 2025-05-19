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
short_names = [t.replace("-USD", "") for t in tickers]

def crawl_latest_crypto_data():
    today = datetime.today()
    
    data = yf.download(tickers, start='2022-01-01', end=today, interval='1d')

    df_close = data['Close'].rename(columns=lambda x: x[:-4])
    df_volume = data['Volume'].rename(columns=lambda x: x[:-4])

    df_raw = df_close.copy()
    for crypto in df_close.columns:
        df_raw[f'{crypto}_Volume'] = df_volume[crypto]

    df_raw = df_raw.reset_index()

    df_raw.to_sql('crypto_raw', engine, if_exists='replace', index=False)
    print(f"Đã lưu dữ liệu thô (close, volume) đến ngày {df_raw['Date'].max()} vào bảng crypto_raw.")


default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 4, 25),
    'retries': 0,
}

with DAG(
    'update_crypto_all',
    default_args=default_args,
    schedule_interval='@daily', 
    catchup=False,
) as dag:

    task_crawl_latest = PythonOperator(
        task_id='crawl_latest_crypto_data',
        python_callable=crawl_latest_crypto_data,
    )

    task_crawl_latest
