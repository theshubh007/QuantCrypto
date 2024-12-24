from src.Data_feed.websocket_feed import DataFeed
from src.app.dashboard import CryptoPriceDashboard
from src.Strategies.moving_average import MovingAverageStrategy
import asyncio
import os


async def main():
    product_ids = ["BTC-USD"]
    data_feed = DataFeed(product_ids)
    dashboard = CryptoPriceDashboard("BTC-USD")

    # Use PORT environment variable or default to 8050
    port = int(os.environ.get("PORT", 8050))
    host = "0.0.0.0"

    print(f"Dashboard will be available at: http://{host}:{port}")

    # Properly await coroutines
    await asyncio.gather(
        data_feed.start(dashboard.app.server),  # Start WebSocket feed
        dashboard.run(),  # Start Dashboard
    )


if __name__ == "__main__":
    asyncio.run(main())
