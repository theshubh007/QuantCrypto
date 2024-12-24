import websockets
import json
from socketio import AsyncServer


class DataFeed:
    def __init__(self, product_ids, limit=1000):
        self.url = "wss://ws-feed.exchange.coinbase.com"
        self.message = {
            "type": "subscribe",
            "product_ids": product_ids,
            "channels": ["ticker"],
        }
        self.price_data = {product: [] for product in product_ids}
        self.limit = limit
        self.sio = AsyncServer(async_mode="asgi")

    async def start(self, app):
        self.sio.attach(app)
        async with websockets.connect(self.url) as websocket:
            await websocket.send(json.dumps(self.message))
            while True:
                response = await websocket.recv()
                await self._update_prices(response)


    async def _update_prices(self, response):
        data = json.loads(response)
        if data.get("type") == "ticker":
            product_id = data.get("product_id")
            price = float(data.get("price", 0))
            if product_id in self.price_data:
                self.price_data[product_id].append(price)
                if len(self.price_data[product_id]) > self.limit:
                    self.price_data[product_id].pop(0)
                await self.sio.emit("price_update", {"product": product_id, "price": price})

    def get_prices(self, product_id):
        return self.price_data.get(product_id, [])
