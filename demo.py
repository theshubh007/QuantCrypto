import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from collections import deque
import websocket
import json
import threading
import time


class CryptoPriceDashboard:
    def __init__(self, symbol="BTC-USD"):
        # Initialize price and time tracking
        self.price_times = deque(maxlen=200)
        self.prices = deque(maxlen=200)

        # Dash app setup
        self.app = dash.Dash(__name__)
        self.app.layout = html.Div(
            [
                html.H1(f"{symbol} Price Tracker"),
                dcc.Graph(id="live-graph", animate=True),
                dcc.Interval(
                    id="graph-update",
                    interval=1000,  # Update every second
                    n_intervals=0,
                ),
            ]
        )

        # Callback for graph update
        self.app.callback(
            Output("live-graph", "figure"), [Input("graph-update", "n_intervals")]
        )(self.update_graph)

        # WebSocket connection details
        self.symbol = symbol
        self.websocket_thread = None
        self.running = False

    def start_websocket(self):
        def on_message(ws, message):
            data = json.loads(message)
            if data.get("type") == "ticker" and data.get("product_id") == self.symbol:
                current_time = int(time.time() * 1000)
                price = float(data.get("price", 0))
                self.price_times.append(current_time)
                self.prices.append(price)

        def on_error(ws, error):
            print(f"WebSocket Error: {error}")

        def on_close(ws, close_status_code, close_msg):
            print("WebSocket Connection Closed")

        def on_open(ws):
            print("WebSocket Connection Opened")
            subscribe_message = json.dumps(
                {
                    "type": "subscribe",
                    "product_ids": [self.symbol],
                    "channels": ["ticker"],
                }
            )
            ws.send(subscribe_message)

        # Create and start WebSocket connection
        self.running = True
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp(
            "wss://ws-feed.exchange.coinbase.com",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        self.websocket_thread = threading.Thread(target=ws.run_forever)
        self.websocket_thread.daemon = True
        self.websocket_thread.start()

    def update_graph(self, n):
        # Create scatter plot with current price data
        data = go.Scatter(
            x=list(self.price_times),
            y=list(self.prices),
            name="Price",
            mode="lines+markers",
        )

        # Dynamically adjust axis ranges
        layout = go.Layout(
            title=f"{self.symbol} Real-Time Price",
            xaxis=dict(
                range=[
                    min(self.price_times) if self.price_times else 0,
                    max(self.price_times) if self.price_times else 0,
                ]
            ),
            yaxis=dict(
                range=[
                    min(self.prices) if self.prices else 0,
                    max(self.prices) if self.prices else 0,
                ]
            ),
        )

        return {"data": [data], "layout": layout}

    def run(self):
        # Start WebSocket and run Dash server
        self.start_websocket()
        self.app.run_server(debug=True, port=8050)


def main():
    dashboard = CryptoPriceDashboard("BTC-USD")
    dashboard.run()


if __name__ == "__main__":
    main()


# http://localhost:8050/
