import asyncio
import websockets
import json
from CryptoDataModel import Ticker


class DataSaver:
    """Fetches ticker data from a WebSocket stream and saves it to a CSV file."""

    def __init__(self, url, product_ids):
        self.url = url
        self.product_ids = product_ids

    async def fetch_data(self):
        """Connects to the WebSocket and fetches ticker data."""
        async with websockets.connect(self.url) as websocket:
            # Subscribe to the ticker channel for the specified product IDs
            subscribe_message = {
                "type": "subscribe",
                "product_ids": self.product_ids,
                "channels": ["ticker"],
            }
            await websocket.send(json.dumps(subscribe_message))

            while True:
                response = await websocket.recv()
                self.process_data(response)

    def process_data(self, response):
        """Processes the received JSON data and saves it to CSV."""
        data = json.loads(response)
        if data.get("type") == "ticker":
            ticker = Ticker.from_dict(data)
            ticker.time = data.get("time")  # Ensure the time is set correctly
            Ticker.write_to_csv(ticker)


if __name__ == "__main__":
    url = "wss://ws-feed.exchange.coinbase.com"  # Example WebSocket URL
    product_ids = ["ETH-USD", "BTC-USD"]  # Example product IDs
    data_saver = DataSaver(url, product_ids)

    # Run the data saver
    asyncio.run(data_saver.fetch_data())
