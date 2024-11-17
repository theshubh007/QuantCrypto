from data_feed import DataFeed
from trading_strategy import PairTradingStrategy

import asyncio

class TradingBot:
    """Coordinates the data feed and trading strategy."""

    def __init__(self, data_feed, strategy):
        self.data_feed = data_feed
        self.strategy = strategy

    async def run(self):
        """Runs the trading bot."""
        # Start data feed in a separate coroutine
        asyncio.create_task(self.data_feed.start())

        while True:
            btc_prices = self.data_feed.get_prices("BTC-USD")
            eth_prices = self.data_feed.get_prices("ETH-USD")
            self.strategy.execute(btc_prices, eth_prices)
            await asyncio.sleep(1)


if __name__ == "__main__":
    product_ids = ["BTC-USD", "ETH-USD"]
    data_feed = DataFeed(product_ids, limit=60)
    strategy = PairTradingStrategy(entry_size=30)
    bot = TradingBot(data_feed, strategy)
    asyncio.run(bot.run())
