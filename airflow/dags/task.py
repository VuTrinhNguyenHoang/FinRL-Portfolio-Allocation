from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from sqlalchemy import create_engine
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import joblib
import os

from stable_baselines3 import PPO
from utils.environment import CryptoPortfolioEnv

db_path = '/opt/airflow/dags/crypto_data.db'
scaler_path = '/opt/airflow/dags/models/scaler.pkl'
ppo_path = '/opt/airflow/dags/models/ppo_crypto_trading_optimized'

engine = create_engine(f'sqlite:///{db_path}')
tickers = ["BTC-USD", "ETH-USD", "ADA-USD", "BNB-USD", "XRP-USD",
           "LTC-USD", "BCH-USD", "EOS-USD", "TRX-USD", "USDT-USD"]
short_names = sorted([t.replace("-USD", "") for t in tickers])

def collect_data():
    data = yf.download(tickers, start='2024-01-01', interval='1d')

    df_close = data['Close'].rename(columns=lambda x: x[:-4])
    df_volume = data['Volume'].rename(columns=lambda x: x[:-4])

    df_raw = df_close.copy()
    for crypto in df_close.columns:
        df_raw[f'{crypto}_Volume'] = df_volume[crypto]

    df_raw = df_raw.reset_index()

    df_raw.to_sql('crypto_raw', engine, if_exists='replace', index=False)
    print(f"Đã lưu dữ liệu thô (close, volume) từ 2024-01-01 đến ngày {df_raw['Date'].max()} vào bảng crypto_raw.")

def calculate_features():
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

    scaler = joblib.load(scaler_path)
    df_feat[df_feat.columns] = scaler.transform(df_feat)

    df_feat = df_feat.reset_index()
    df_merged = pd.merge(df_raw[df_raw.columns[:10]], df_feat, on='Date', how='inner')

    df_merged.to_sql('crypto_features', engine, if_exists='replace', index=False)
    print(f"Đã lưu dữ liệu tính toán các chỉ báo kỹ thuật vào bảng crypto_features.") 

def agent_action():
    features = pd.read_sql('SELECT * FROM crypto_features', engine, parse_dates=['Date'])
    features.index = pd.to_datetime(features['Date']).dt.date
    features.drop(columns=['Date'], inplace=True)

    model = PPO.load(ppo_path)

    inital_cash = 10000
    ppo_value = [inital_cash]
    btc_value = [inital_cash]
    equal_value = [inital_cash]
    weights_history = []
    equal_weights = np.ones(len(tickers)) / len(tickers)
    tickers_test = ["BTC", "ETH", "ADA", "BNB", "XRP", "LTC", "BCH", "EOS", "TRX", "USDT"]

    env = CryptoPortfolioEnv(features, tickers_test)
    obs = env.reset()
    for t in range(env.max_steps):
        action, _ = model.predict(obs, deterministic=True)

        next_obs, reward, done, info = env.step(action)

        weights = action.copy()
        weights_history.append(weights)

        ppo_value.append(env.portfolio_value)

        btc_return = features[tickers_test].pct_change().iloc[t + 1][tickers_test.index("BTC")]
        btc_value.append(btc_value[-1] * (1 + btc_return) if not np.isnan(btc_return) else btc_value[-1])
        
        equal_return = np.dot(equal_weights, features[tickers_test].pct_change().iloc[t + 1])
        equal_value.append(equal_value[-1] * (1 + equal_return) if not np.isnan(equal_return) else equal_value[-1])
        
        obs = next_obs
        if done:
            break

    dates = features.index[1:]
    ppo_value = ppo_value[1:]
    btc_value = btc_value[1:]
    equal_value = equal_value[1:]

    result_df = pd.DataFrame({
        'Date': dates,
        'PPO Value': ppo_value,
        'BTC Value': btc_value,
        'Equal-Weighted Value': equal_value
    })

    result_df.to_sql('portfolio_value', engine, if_exists='replace', index=False)

    action_df = pd.DataFrame(weights_history, columns=short_names)
    action_df['Date'] = list(dates)
    action_df = action_df[['Date'] + short_names]

    action_df.to_sql('action_weights', engine, if_exists='replace', index=False)

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

    task_collect_data = PythonOperator(
        task_id='collect_data',
        python_callable=collect_data
    )

    task_cal_feat = PythonOperator(
        task_id='calculate_features',
        python_callable=calculate_features
    )

    task_agent = PythonOperator(
        task_id='agent_action',
        python_callable=agent_action
    )

    task_collect_data >> task_cal_feat >> task_agent