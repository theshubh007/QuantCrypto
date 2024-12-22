class TickerData:
    """Data model for managing ticker data."""

    def __init__(self, data):
        """Initialize the TickerData object with the provided data."""
        self.type = data.get("type")
        self.sequence = data.get("sequence")
        self.product_id = data.get("product_id")
        self.price = float(data.get("price"))
        self.open_24h = float(data.get("open_24h"))
        self.volume_24h = float(data.get("volume_24h"))
        self.low_24h = float(data.get("low_24h"))
        self.high_24h = float(data.get("high_24h"))
        self.volume_30d = float(data.get("volume_30d"))
        self.best_bid = float(data.get("best_bid"))
        self.best_bid_size = float(data.get("best_bid_size"))
        self.best_ask = float(data.get("best_ask"))
        self.best_ask_size = float(data.get("best_ask_size"))
        self.side = data.get("side")
        self.time = data.get("time")
        self.trade_id = data.get("trade_id")
        self.last_size = float(data.get("last_size"))

    def update(self, data):
        """Update the ticker data with new values."""
        self.price = float(data.get("price", self.price))
        self.open_24h = float(data.get("open_24h", self.open_24h))
        self.volume_24h = float(data.get("volume_24h", self.volume_24h))
        self.low_24h = float(data.get("low_24h", self.low_24h))
        self.high_24h = float(data.get("high_24h", self.high_24h))
        self.volume_30d = float(data.get("volume_30d", self.volume_30d))
        self.best_bid = float(data.get("best_bid", self.best_bid))
        self.best_bid_size = float(data.get("best_bid_size", self.best_bid_size))
        self.best_ask = float(data.get("best_ask", self.best_ask))
        self.best_ask_size = float(data.get("best_ask_size", self.best_ask_size))
        self.side = data.get("side", self.side)
        self.time = data.get("time", self.time)
        self.trade_id = data.get("trade_id", self.trade_id)
        self.last_size = float(data.get("last_size", self.last_size))

    def display(self):
        """Display the ticker data."""
        print(f"Product ID: {self.product_id}")
        print(f"Price: {self.price}")
        print(f"Open 24h: {self.open_24h}")
        print(f"Volume 24h: {self.volume_24h}")
        print(f"Low 24h: {self.low_24h}")
        print(f"High 24h: {self.high_24h}")
        print(f"Best Bid: {self.best_bid}")
        print(f"Best Ask: {self.best_ask}")
        print(f"Side: {self.side}")
        print(f"Time: {self.time}")
        print(f"Trade ID: {self.trade_id}")
        print(f"Last Size: {self.last_size}")
