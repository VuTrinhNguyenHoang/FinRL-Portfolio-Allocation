import numpy as np
import gym
from gym import spaces

class CryptoPortfolioEnv(gym.Env):
    def __init__(self, df, tickers):
        super(CryptoPortfolioEnv, self).__init__()
        self.df = df
        self.tickers = tickers
        self.action_space = spaces.Box(low=-1, high=1, shape=(len(tickers),), dtype=np.float32)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(len(df.drop(columns=tickers).columns),), dtype=np.float32)
        self.current_step = 0
        self.max_steps = len(df) - 1
        self.returns = df[tickers].pct_change().dropna().values
        self.state_data = df.drop(columns=tickers).values
        self.portfolio_value = 10000
        self.previous_weights = np.zeros(len(tickers))
        self.returns_history = []

    def reset(self):
        self.current_step = 0
        self.portfolio_value = 10000
        self.previous_weights = np.zeros(len(self.tickers))
        self.returns_history = []
        return self.state_data[self.current_step]

    def step(self, action):
        weights = action.copy()

        # Kiểm soát shorting: Không short nếu giá tăng > 5%
        for i, weight in enumerate(weights):
            if weight < 0 and self.returns[self.current_step, i] > 0.05:
                weights[i] = 0
        
        # Hạn chế tổng trọng số âm (không quá 50%)
        total_short = sum(abs(w) for w in weights if w < 0)
        if total_short > 0.2:
            weights = weights * (0.2 / (total_short + 1e-6))

        # Chuẩn hóa trọng số
        weights = weights / (np.sum(np.abs(weights)) + 1e-6)

        # Tính lợi nhuận danh mục
        portfolio_return = np.dot(weights, self.returns[self.current_step])

        # Tính chi phí shorting
        borrowing_fee = 0.0005
        short_costs = sum(abs(weight) * borrowing_fee for weight in weights if weight < 0)
        portfolio_return -= short_costs

        # Tính phí giao dịch
        transaction_cost = 0.002
        weight_changes = sum(abs(weights - self.previous_weights))
        portfolio_return -= transaction_cost * weight_changes

        # Cập nhật giá trị danh mục
        self.portfolio_value *= (1 + portfolio_return)
        self.returns_history.append(portfolio_return)

        # Tính volatility
        if len(self.returns_history) >= 50:
            volatility = np.std(self.returns_history[-50:]) * np.sqrt(252)
        else:
            volatility = 0.05

        # Tính phần thưởng dựa trên sharpe ratio
        reward = portfolio_return / (volatility + 1e-6)

        # Hình phạt cho sự ổn định của trọng số
        reward -= 0.02 * weight_changes

        # Hình phạt cho drawdown lớn
        max_value = max(self.portfolio_value, max(self.returns_history, default=self.portfolio_value))
        drawdown = (max_value - self.portfolio_value) / max_value
        reward -= 0.1 * abs(drawdown)

        self.previous_weights = weights.copy()
        self.current_step += 1
        done = self.current_step >= self.max_steps or self.portfolio_value < 0.3 * 10000 # Dừng nếu thua lỗ quá 90%
        obs = self.state_data[self.current_step] if not done else np.zeros_like(self.state_data[0])
        return obs, reward, done, {}