import asyncio
import websockets
import json


class DataFeed:
    """Handles WebSocket data feed and maintains price history."""

    def __init__(self, product_ids, limit):
        self.url = "wss://ws-feed.exchange.coinbase.com"
        self.message = {
            "type": "subscribe",
            "product_ids": product_ids,
            "channels": ["ticker"],
        }
        self.price_data = {product: [] for product in product_ids}
        self.limit = limit

    async def start(self):
        """Starts the WebSocket feed."""
        async with websockets.connect(self.url) as websocket:
            await websocket.send(json.dumps(self.message))
            while True:
                response = await websocket.recv()
                self._update_prices(response)

    def _update_prices(self, response):
        """Updates price history based on WebSocket response."""
        data = json.loads(response)
        if data.get("type") == "ticker":
            ticker = data.get("product_id")
            price = float(data.get("price", 0))
            if ticker in self.price_data:
                self.price_data[ticker].append(price)
                # Limit the size of the price history
                if len(self.price_data[ticker]) > self.limit:
                    self.price_data[ticker].pop(0)

    def get_prices(self, product_id):
        """Returns the price history of a product."""
        return self.price_data.get(product_id, [])
