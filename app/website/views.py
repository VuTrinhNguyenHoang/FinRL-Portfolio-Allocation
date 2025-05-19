from flask import Blueprint, render_template, jsonify
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

views = Blueprint('views', __name__)

db_path = "/opt/crypto_data.db"
engine = create_engine(f'sqlite:///{db_path}')

df_w = pd.read_sql('SELECT * FROM action_weights', engine, parse_dates=['Date'])
df_p = pd.read_sql('SELECT * FROM portfolio_value', engine, parse_dates=['Date'])

def calculate_annual_return(portfolio_values):
    days = (portfolio_values.index[-1] - portfolio_values.index[0]).days
    if days <= 0:
        return 0
    
    total_return = portfolio_values.iloc[-1] / portfolio_values.iloc[0] - 1
    
    annual_return = (1 + total_return) ** (365 / days) - 1
    return annual_return

def calculate_daily_returns(portfolio_values):
    return portfolio_values.pct_change().dropna()

def calculate_volatility(portfolio_values):
    daily_returns = calculate_daily_returns(portfolio_values)
    return daily_returns.std() * np.sqrt(252)

def calculate_sharpe_ratio(portfolio_values, risk_free_rate=0.02):
    annual_return = calculate_annual_return(portfolio_values)
    volatility = calculate_volatility(portfolio_values)
    if volatility == 0:
        return 0
    
    return (annual_return - risk_free_rate) / volatility

def calculate_max_drawdown(portfolio_values):
    rolling_max = portfolio_values.cummax()
    drawdowns = (portfolio_values / rolling_max - 1)
    max_drawdown = drawdowns.min()
    return max_drawdown

def update_metrics_data():
    start_date = df_p['Date'].min().strftime('%Y-%m-%d')
    end_date = df_p['Date'].max().strftime('%Y-%m-%d')
    
    ppo_values = df_p.set_index('Date')['PPO Value']
    btc_values = df_p.set_index('Date')['BTC Value']
    equal_values = df_p.set_index('Date')['Equal-Weighted Value']
    
    metrics = pd.DataFrame({
        'strategy': ['PPO Strategy', 'BTC Only', 'Equal Weight'],
        'start_period': [start_date, start_date, start_date],
        'end_period': [end_date, end_date, end_date],
        'cumulative_return': [
            f"{(ppo_values.iloc[-1] / ppo_values.iloc[0] - 1) * 100:.2f}%", 
            f"{(btc_values.iloc[-1] / btc_values.iloc[0] - 1) * 100:.2f}%", 
            f"{(equal_values.iloc[-1] / equal_values.iloc[0] - 1) * 100:.2f}%"
        ],
        'annual_return': [
            f"{calculate_annual_return(ppo_values) * 100:.2f}%",
            f"{calculate_annual_return(btc_values) * 100:.2f}%",
            f"{calculate_annual_return(equal_values) * 100:.2f}%"
        ],
        'sharpe_ratio': [
            round(calculate_sharpe_ratio(ppo_values), 2),
            round(calculate_sharpe_ratio(btc_values), 2),
            round(calculate_sharpe_ratio(equal_values), 2)
        ],
        'max_drawdown': [
            f"{calculate_max_drawdown(ppo_values) * 100:.2f}%",
            f"{calculate_max_drawdown(btc_values) * 100:.2f}%",
            f"{calculate_max_drawdown(equal_values) * 100:.2f}%"
        ],
        'volatility': [
            f"{calculate_volatility(ppo_values) * 100:.2f}%",
            f"{calculate_volatility(btc_values) * 100:.2f}%",
            f"{calculate_volatility(equal_values) * 100:.2f}%"
        ]
    })
    
    return metrics

df_metrics = update_metrics_data()

@views.route('/')
def index():
    return render_template('index.html')

@views.route('/api/data')
def api_data():
    # chuyển datetime thành string
    w = df_w.copy()
    w['Date'] = w['Date'].dt.strftime('%Y-%m-%d')
    p = df_p.copy()
    p['Date'] = p['Date'].dt.strftime('%Y-%m-%d')

    data = {
        'weights': w.to_dict(orient='records'),
        'portfolio': p.to_dict(orient='records'),
        'metrics': df_metrics.to_dict(orient='records')
    }
    return jsonify(data)
