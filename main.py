from src.Data_feed.websocket_feed import DataFeed
from src.app.dashboard import CryptoPriceDashboard
from src.Strategies.moving_average import MovingAverageStrategy
import asyncio


async def main():
    product_ids = ["BTC-USD"]
    data_feed = DataFeed(product_ids)
    
    dashboard = CryptoPriceDashboard("BTC-USD")
    # Define the host and port
    host = "localhost"
    port = 8050

    # Print the dashboard address
    print(f"Dashboard will be available at: http://{host}:{port}")

    await asyncio.gather(data_feed.start(dashboard.app.server), dashboard.run())


if __name__ == "__main__":
    print("Starting main")
    
    asyncio.run(main())
