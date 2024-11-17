import math
from statistics import mean, stdev


class TradingStrategy:
    """Base class for trading strategies."""

    def __init__(self, entry_size):
        self.entry_size = entry_size
        self.side = "neutral"

    def calculate_ror(self, prices):
        """Calculates the rate of return for a price series."""
        return [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]

    def calculate_pnl(self, prices, old_price, tx=0.0045):
        """Calculates the profit or loss for a trade."""
        current_price = prices[-1]
        return (current_price * (1 - tx)) / (old_price * (1 + tx)) - 1.0


class PairTradingStrategy(TradingStrategy):
    """Implements pair trading strategy using Z-Score signals."""

    def __init__(self, entry_size):
        super().__init__(entry_size)
        self.btc_price = 0
        self.eth_price = 0
        self.btc_ror = 1
        self.eth_ror = 1

    def calculate_signal(self, rx, ex):
        """
        Calculates the Z-Score signal for trading based on the linear regression model
        between two datasets: 'rx' (the return of the asset you're analyzing) and 'ex'
        (the return of a benchmark or another asset you're comparing to).

        The function calculates the Z-score of the spread between the actual return of
        'ex' and the predicted return based on a linear regression of 'ex' on 'rx'.
        The Z-score represents how far the current spread is from the average spread
        in terms of standard deviations, providing a signal for trading.

        Parameters:
        rx (list): A list of numerical values representing the return of the asset.
        ex (list): A list of numerical values representing the return of the benchmark
                  or another asset you're comparing against.

        Returns:
        float: The Z-score of the spread between 'ex' and its predicted value from
              the linear regression of 'ex' on 'rx'.

        Steps:
        1. Calculate Beta (slope) using the formula:
          β = Σ((rx[i] - mean(rx)) * (ex[i] - mean(ex))) / Σ((rx[i] - mean(rx))^2)
          - This represents the relationship between 'rx' and 'ex'.

        2. Calculate Alpha (intercept) using the formula:
          α = mean(ex) - β * mean(rx)
          - This represents the value of 'ex' when 'rx' is zero.

        3. Calculate the spread as the difference between the actual value of 'ex'
          and the predicted value from the regression line for each data point:
          spread[i] = ex[i] - (α + β * rx[i])

        4. Calculate the Z-score of the spread:
          Z-score = (spread[-1] - mean(spread)) / stdev(spread)
          - This represents how far the last spread is from the mean of the spread,
            measured in standard deviations.

        Example:
        rx = [0.01, 0.02, -0.01, 0.05, 0.04]
        ex = [0.02, 0.03, 0.00, 0.04, 0.05]
        z_score = calculate_signal(rx, ex)
        print(z_score)

        """
        # Calculate Beta
        beta = sum(
            (rx[i] - mean(rx)) * (ex[i] - mean(ex)) for i in range(len(rx))
        ) / sum((rx[i] - mean(rx)) ** 2 for i in range(len(rx)))

        # Calculate Alpha
        alpha = mean(ex) - beta * mean(rx)

        # Calculate the spread between the actual 'ex' and the predicted 'ex'
        spread = [ex[i] - (alpha + beta * rx[i]) for i in range(len(rx))]

        # Calculate the Z-score of the spread
        z_score = (spread[-1] - mean(spread)) / stdev(spread)

        return z_score

    def execute(self, btc_prices, eth_prices):
        """Executes trading logic based on Z-Score."""
        if len(btc_prices) >= self.entry_size and len(eth_prices) >= self.entry_size:
            # Align price series
            n, m = len(btc_prices), len(eth_prices)
            xbtc = btc_prices[-min(n, m) :]
            xeth = eth_prices[-min(n, m) :]

            # Calculate returns
            rx = self.calculate_ror(xbtc)
            ex = self.calculate_ror(xeth)

            # Calculate Z-Score signal
            z_score = self.calculate_signal(rx, ex)

            # Trading logic
            if z_score < -1.96 and self.side == "short":
                self.side = "neutral"
                self.eth_ror *= 1 + self.calculate_pnl(xeth, self.eth_price)
                print(f"Profit for Ethereum: {self.eth_ror - 1:.2%}")

            if z_score > 1.96 and self.side == "neutral":
                self.side = "short"
                self.eth_price = xeth[-1]
                print("Go Short in Ethereum")

            if z_score > 1.96 and self.side == "long":
                self.side = "neutral"
                self.btc_ror *= 1 + self.calculate_pnl(xbtc, self.btc_price)
                print(f"Profit for Bitcoin: {self.btc_ror - 1:.2%}")

            if z_score < -1.96 and self.side == "neutral":
                self.side = "long"
                self.btc_price = xbtc[-1]
                print("Go Long in Bitcoin")

        else:
            print(
                f"Insufficient data for trading. BTC: {len(btc_prices)}, ETH: {len(eth_prices)}"
            )
