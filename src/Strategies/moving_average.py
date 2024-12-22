# class MovingAverageStrategy:
#     def __init__(
#         self, short_window=10, long_window=50, trading_fee=0.001, tax_rate=0.02
#     ):
#         self.short_window = short_window
#         self.long_window = long_window
#         self.trading_fee = trading_fee
#         self.tax_rate = tax_rate

#     def calculate_signals(self, prices):
#         """Calculate buy/sell signals based on moving average crossover."""
#         if len(prices) < self.long_window:
#             return None

#         short_ma = sum(prices[-self.short_window :]) / self.short_window
#         long_ma = sum(prices[-self.long_window :]) / self.long_window

#         if short_ma > long_ma:
#             return "buy"
#         elif short_ma < long_ma:
#             return "sell"
#         return None

#     def calculate_profit_loss(self, initial_balance, trades):
#         """Calculate profit/loss after applying fees and taxes."""
#         balance = initial_balance
#         for trade in trades:
#             action, price = trade["action"], trade["price"]
#             if action == "buy":
#                 balance -= price + price * self.trading_fee
#             elif action == "sell":
#                 balance += price - price * (self.trading_fee + self.tax_rate)
#         return balance - initial_balance


class MovingAverageStrategy:
    def __init__(
        self, short_window=10, long_window=50, trading_fee=0.001, tax_rate=0.02
    ):
        self.short_window = short_window
        self.long_window = long_window
        self.trading_fee = trading_fee  # 0.1% per trade
        self.tax_rate = tax_rate  # 2% on profits

        # Trade tracking
        self.trades = []
        self.position = None  # None = no position, 'long' = holding coins
        self.entry_price = None
        self.current_balance = 0
        self.initial_balance = 0
        self.total_fees_paid = 0
        self.total_taxes_paid = 0

    def calculate_signals(self, prices):
        """Calculate buy/sell signals based on moving average crossover."""
        if len(prices) < self.long_window:
            return None

        short_ma = sum(prices[-self.short_window :]) / self.short_window
        long_ma = sum(prices[-self.long_window :]) / self.long_window

        if short_ma > long_ma:
            return "buy"
        elif short_ma < long_ma:
            return "sell"
        return None

    def execute_trade(self, signal, current_price, timestamp, investment_amount=1000):
        """
        Execute a trade based on the signal and track P&L.

        Args:
            signal: 'buy' or 'sell' signal
            current_price: Current price of the asset
            timestamp: Time of the trade
            investment_amount: Amount to invest per trade in USD
        """
        if self.initial_balance == 0:
            self.initial_balance = investment_amount
            self.current_balance = investment_amount

        if signal == "buy" and self.position is None:
            # Calculate how many coins we can buy with our investment amount
            fee = investment_amount * self.trading_fee
            coins = (investment_amount - fee) / current_price

            self.position = "long"
            self.entry_price = current_price
            self.total_fees_paid += fee

            trade = {
                "type": "buy",
                "price": current_price,
                "coins": coins,
                "timestamp": timestamp,
                "fee": fee,
                "investment": investment_amount,
            }
            self.trades.append(trade)

        elif signal == "sell" and self.position == "long":
            # Find the last buy trade to calculate coins to sell
            last_buy = next(
                trade for trade in reversed(self.trades) if trade["type"] == "buy"
            )
            coins_to_sell = last_buy["coins"]

            # Calculate sale proceeds
            gross_proceeds = coins_to_sell * current_price
            fee = gross_proceeds * self.trading_fee

            # Calculate profit/loss and taxes
            profit = gross_proceeds - last_buy["investment"]
            tax = max(0, profit * self.tax_rate)  # Tax only on profits

            net_proceeds = gross_proceeds - fee - tax

            self.current_balance = net_proceeds
            self.total_fees_paid += fee
            self.total_taxes_paid += tax
            self.position = None

            trade = {
                "type": "sell",
                "price": current_price,
                "coins": coins_to_sell,
                "timestamp": timestamp,
                "fee": fee,
                "tax": tax,
                "gross_proceeds": gross_proceeds,
                "net_proceeds": net_proceeds,
                "profit_loss": net_proceeds - last_buy["investment"],
            }
            self.trades.append(trade)

    def get_performance_metrics(self):
        """
        Calculate and return comprehensive performance metrics.
        """
        if not self.trades:
            return {
                "total_trades": 0,
                "current_balance": self.initial_balance,
                "total_profit_loss": 0,
                "total_fees": 0,
                "total_taxes": 0,
                "return_percentage": 0,
                "position": "No position",
            }

        total_profit_loss = self.current_balance - self.initial_balance

        metrics = {
            "total_trades": len(self.trades),
            "current_balance": round(self.current_balance, 2),
            "total_profit_loss": round(total_profit_loss, 2),
            "total_fees": round(self.total_fees_paid, 2),
            "total_taxes": round(self.total_taxes_paid, 2),
            "return_percentage": round(
                (total_profit_loss / self.initial_balance) * 100, 2
            ),
            "position": self.position if self.position else "No position",
        }

        # Calculate win rate
        if len(self.trades) > 0:
            profitable_trades = sum(
                1
                for trade in self.trades
                if trade.get("type") == "sell" and trade.get("profit_loss", 0) > 0
            )
            total_closed_trades = sum(
                1 for trade in self.trades if trade.get("type") == "sell"
            )

            if total_closed_trades > 0:
                metrics["win_rate"] = round(
                    (profitable_trades / total_closed_trades) * 100, 2
                )
            else:
                metrics["win_rate"] = 0

        return metrics

    def get_trade_history(self):
        """
        Return formatted trade history with key metrics for each trade.
        """
        formatted_trades = []
        for trade in self.trades:
            formatted_trade = {
                "timestamp": trade["timestamp"],
                "type": trade["type"],
                "price": round(trade["price"], 2),
                "coins": round(trade["coins"], 8),
                "fee": round(trade["fee"], 2),
            }

            if trade["type"] == "sell":
                formatted_trade.update(
                    {
                        "profit_loss": round(trade["profit_loss"], 2),
                        "tax": round(trade["tax"], 2),
                        "net_proceeds": round(trade["net_proceeds"], 2),
                    }
                )

            formatted_trades.append(formatted_trade)

        return formatted_trades
