import csv


class Ticker:
    """Represents the ticker data for a cryptocurrency."""

    def __init__(
        self,
        product_id,
        price,
        open_24h,
        volume_24h,
        low_24h,
        high_24h,
        volume_30d,
        best_bid,
        best_bid_size,
        best_ask,
        best_ask_size,
        side,
        time,
        trade_id,
        last_size,
    ):
        self.product_id = product_id
        self.price = float(price)  # Convert price to float
        self.open_24h = float(open_24h)
        self.volume_24h = float(volume_24h)
        self.low_24h = float(low_24h)
        self.high_24h = float(high_24h)
        self.volume_30d = float(volume_30d)
        self.best_bid = float(best_bid)
        self.best_bid_size = float(best_bid_size)
        self.best_ask = float(best_ask)
        self.best_ask_size = float(best_ask_size)
        self.side = side
        self.time = time
        self.trade_id = trade_id
        self.last_size = float(last_size)

    @classmethod
    def from_dict(cls, data):
        """Creates a Ticker instance from a dictionary."""
        return cls(
            product_id=data.get("product_id"),
            price=data.get("price"),
            open_24h=data.get("open_24h"),
            volume_24h=data.get("volume_24h"),
            low_24h=data.get("low_24h"),
            high_24h=data.get("high_24h"),
            volume_30d=data.get("volume_30d"),
            best_bid=data.get("best_bid"),
            best_bid_size=data.get("best_bid_size"),
            best_ask=data.get("best_ask"),
            best_ask_size=data.get("best_ask_size"),
            side=data.get("side"),
            time=data.get("time"),
            trade_id=data.get("trade_id"),
            last_size=data.get("last_size"),
        )

    def to_csv_row(self):
        """Returns a CSV row representation of the ticker data."""
        return [
            self.time,
            self.product_id,
            self.price,
            self.open_24h,
            self.volume_24h,
            self.low_24h,
            self.high_24h,
            self.volume_30d,
            self.best_bid,
            self.best_bid_size,
            self.best_ask,
            self.best_ask_size,
            self.side,
            self.trade_id,
            self.last_size,
        ]

    @staticmethod
    def write_to_csv(
        ticker_data,
        filename=r"D:\project\finallevelprojects\Stock_Crypto_Project_Hub\QuantCrypto\ticker_data.csv",
    ):
        """Writes a list of Ticker instances to a CSV file."""
        with open(filename, mode="a", newline="") as file:
            writer = csv.writer(file)
            # Write header if the file is empty
            if file.tell() == 0:
                writer.writerow(
                    [
                        "Timestamp",
                        "Product ID",
                        "Price",
                        "Open 24h",
                        "Volume 24h",
                        "Low 24h",
                        "High 24h",
                        "Volume 30d",
                        "Best Bid",
                        "Best Bid Size",
                        "Best Ask",
                        "Best Ask Size",
                        "Side",
                        "Trade ID",
                        "Last Size",
                    ]
                )
            # Write the ticker data
            writer.writerow(ticker_data.to_csv_row())
