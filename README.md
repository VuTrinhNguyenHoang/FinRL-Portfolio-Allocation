# FinRL-Portfolio-Allocation

## Overview

FinRL-Portfolio-Allocation is a Reinforcement Learning project for optimizing cryptocurrency portfolio allocation. The system uses the PPO (Proximal Policy Optimization) algorithm to learn how to allocate capital among multiple cryptocurrencies to maximize returns and minimize risk.

![Crypto Portfolio Optimization](https://img.shields.io/badge/Crypto-Portfolio%20Optimization-blue)
![Reinforcement Learning](https://img.shields.io/badge/AI-Reinforcement%20Learning-green)
![Docker](https://img.shields.io/badge/DevOps-Docker-blue)
![Airflow](https://img.shields.io/badge/Pipeline-Airflow-red)

## Features

- **Automated Trading System**: Uses a PPO model from the Stable Baselines3 library to make portfolio allocation decisions
- **Portfolio Optimization**: Allocates capital across multiple cryptocurrencies to maximize risk-adjusted returns
- **Performance Tracking**: Visual dashboard displaying portfolio value and performance metrics
- **Automated Pipeline**: Uses Apache Airflow to automate data collection and trading

## System Architecture

The project consists of two main components:

1. **Airflow Pipeline**:
   - Collects cryptocurrency data from Yahoo Finance
   - Calculates technical indicators
   - Runs the RL model to determine optimal allocation weights
   - Saves results to a database

2. **Web Dashboard**: Displays portfolio performance and compares with baseline strategies
   - Shows portfolio value over time
   - Tracks allocation weights for each cryptocurrency
   - Compares PPO strategy with BTC-only and equal-weight strategies

## Requirements

- Docker and Docker Compose
- Python 3.10+
- Python libraries:
  - stable-baselines3
  - pandas
  - numpy
  - scikit-learn
  - yfinance
  - Flask
  - pandas_ta
  - sqlalchemy

## Installation

1. Clone repository:
```bash
git clone https://github.com/VuTrinhNguyenHoang/FinRL-Portfolio-Allocation.git
cd FinRL-Portfolio-Allocation
```

2. Start Docker containers:
```bash
docker-compose up -d
```

3. Access services:
   - Airflow: http://localhost:8080 (username: airflow, password: airflow)
   - Web Dashboard: http://localhost:8000

## Project Structure

```
FinRL-Portfolio-Allocation/
├── airflow/                     # Apache Airflow configuration
│   ├── dags/                    # Airflow DAGs for data pipeline
│   │   ├── task.py              # Main pipeline for data processing and simulation
│   │   ├── models/              # Trained models
│   │   └── utils/               # Utility components
│   ├── logs/                    # Log files
│   ├── plugins/                 # Airflow plugins
│   ├── scripts/                 # Support scripts
│   ├── dockerfile               # Dockerfile for Airflow
│   └── requirements.txt         # Airflow dependencies
├── app/                         # Web application
│   ├── website/                 # Flask app
│   │   ├── templates/           # HTML templates
│   │   ├── static/              # CSS/JS files
│   │   ├── views.py             # Web routes
│   │   └── __init__.py          # App initialization
│   ├── dockerfile               # Dockerfile for web app
│   ├── main.py                  # Entry point for web app
│   └── requirements.txt         # Web app dependencies
├── docker-compose.yml           # Docker Compose configuration
└── README.md                    # Project documentation
```

## Usage

1. **Portfolio Monitoring**:
   - Access the dashboard at http://localhost:8000
   - View portfolio value, allocation weights, and performance metrics

2. **Pipeline Management**:
   - Access Airflow at http://localhost:8080
   - Trigger DAGs to collect new data and update allocations

## RL Algorithm

The project uses the Proximal Policy Optimization (PPO) algorithm with the following characteristics:
- **State**: Technical indicators (MACD, RSI, Bollinger Bands, Volume, Volatility)
- **Action**: Allocation weights for each cryptocurrency (including shorting if necessary)
- **Reward**: Based on Sharpe ratio, taking into account drawdowns and transaction costs

## Performance Comparison

The system compares the RL strategy with two baseline strategies:
1. **BTC Only**: 100% investment in Bitcoin
2. **Equal Weight**: Equal allocation of capital across all cryptocurrencies

Evaluation metrics:
- Cumulative and annual returns
- Sharpe ratio
- Volatility
- Max Drawdown

## References

- [FinRL: Financial Reinforcement Learning](https://github.com/AI4Finance-Foundation/FinRL)
- [Stable Baselines3](https://github.com/DLR-RM/stable-baselines3)
- [Apache Airflow](https://airflow.apache.org/)