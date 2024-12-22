def calculate_net_profit(initial_balance, trades, fee, tax):
    """Calculate net profit after fees and taxes."""
    balance = initial_balance
    for trade in trades:
        action, price = trade["action"], trade["price"]
        if action == "buy":
            balance -= price + price * fee
        elif action == "sell":
            balance += price - price * (fee + tax)
    return balance - initial_balance
