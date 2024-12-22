import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from collections import deque
import websocket
import json
import threading
import time
import numpy as np
from datetime import datetime
from src.Strategies.moving_average import MovingAverageStrategy


class CryptoPriceDashboard:
    def __init__(
        self, symbol="BTC-USD", short_window=10, long_window=50, investment_amount=1000
    ):
        # Initialize price and time tracking
        self.price_times = deque(maxlen=200)
        self.prices = deque(maxlen=200)
        self.investment_amount = investment_amount

        # Initialize strategy
        self.strategy = MovingAverageStrategy(short_window, long_window)
        self.short_ma = deque(maxlen=200)
        self.long_ma = deque(maxlen=200)
        self.signals = deque(maxlen=200)

        # Dash app setup
        self.app = dash.Dash(__name__)
        self.app.layout = html.Div(
            [
                # Header Section
                html.Div(
                    [
                        html.H1(f"{symbol} Price Tracker with Moving Average Strategy"),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3(
                                            "Account Overview",
                                            className="text-xl font-bold",
                                        ),
                                        html.Div(
                                            id="account-metrics",
                                            className="grid grid-cols-2 gap-4",
                                        ),
                                    ],
                                    className="bg-white p-4 rounded-lg shadow",
                                )
                            ],
                            className="mb-4",
                        ),
                    ]
                ),
                # Main Chart
                dcc.Graph(id="live-graph", animate=True),
                # Trading Signals and Performance
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3("Current Trading Signal"),
                                html.Div(
                                    id="signal-output", className="text-lg font-bold"
                                ),
                            ],
                            className="bg-white p-4 rounded-lg shadow mb-4",
                        ),
                        html.Div(
                            [
                                html.H3("Recent Trades"),
                                html.Div(
                                    id="trade-history", className="overflow-x-auto"
                                ),
                            ],
                            className="bg-white p-4 rounded-lg shadow",
                        ),
                    ]
                ),
                dcc.Interval(
                    id="graph-update",
                    interval=1000,
                    n_intervals=0,
                ),
            ],
            className="p-4 bg-gray-100",
        )

        # Callbacks
        self.app.callback(
            [
                Output("live-graph", "figure"),
                Output("signal-output", "children"),
                Output("account-metrics", "children"),
                Output("trade-history", "children"),
            ],
            [Input("graph-update", "n_intervals")],
        )(self.update_graph_and_signal)

        # WebSocket connection details
        self.symbol = symbol
        self.websocket_thread = None
        self.running = False

    def format_currency(self, value):
        """Format currency values with $ and 2 decimal places"""
        return f"${value:,.2f}"

    def create_metrics_cards(self, metrics):
        """Create metric cards for account overview"""
        cards = []

        # Balance Card
        cards.extend(
            [
                html.Div(
                    [
                        html.H4("Current Balance", className="text-sm text-gray-600"),
                        html.P(
                            self.format_currency(metrics["current_balance"]),
                            className="text-lg font-bold",
                        ),
                    ],
                    className="bg-white p-3 rounded shadow",
                ),
                html.Div(
                    [
                        html.H4("Total P&L", className="text-sm text-gray-600"),
                        html.P(
                            self.format_currency(metrics["total_profit_loss"]),
                            className=f"text-lg font-bold {'text-green-600' if metrics['total_profit_loss'] >= 0 else 'text-red-600'}",
                        ),
                    ],
                    className="bg-white p-3 rounded shadow",
                ),
                html.Div(
                    [
                        html.H4("Return %", className="text-sm text-gray-600"),
                        html.P(
                            f"{metrics['return_percentage']}%",
                            className=f"text-lg font-bold {'text-green-600' if metrics['return_percentage'] >= 0 else 'text-red-600'}",
                        ),
                    ],
                    className="bg-white p-3 rounded shadow",
                ),
                html.Div(
                    [
                        html.H4("Win Rate", className="text-sm text-gray-600"),
                        html.P(
                            f"{metrics.get('win_rate', 0)}%",
                            className="text-lg font-bold",
                        ),
                    ],
                    className="bg-white p-3 rounded shadow",
                ),
            ]
        )

        return cards

    def create_trade_history_table(self, trades):
        """Create trade history table"""
        if not trades:
            return html.P("No trades yet")

        return html.Table(
            [
                # Table Header
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Time", className="p-2"),
                            html.Th("Type", className="p-2"),
                            html.Th("Price", className="p-2"),
                            html.Th("Amount", className="p-2"),
                            html.Th("P&L", className="p-2"),
                        ],
                        className="bg-gray-100",
                    )
                ),
                # Table Body
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td(
                                    datetime.fromtimestamp(
                                        trade["timestamp"] / 1000
                                    ).strftime("%H:%M:%S"),
                                    className="p-2",
                                ),
                                html.Td(
                                    trade["type"].upper(),
                                    className="p-2 font-bold "
                                    + (
                                        "text-green-600"
                                        if trade["type"] == "buy"
                                        else "text-red-600"
                                    ),
                                ),
                                html.Td(
                                    self.format_currency(trade["price"]),
                                    className="p-2",
                                ),
                                html.Td(f"{trade['coins']:.8f}", className="p-2"),
                                html.Td(
                                    (
                                        self.format_currency(
                                            trade.get("profit_loss", 0)
                                        )
                                        if "profit_loss" in trade
                                        else "-"
                                    ),
                                    className="p-2 "
                                    + (
                                        "text-green-600"
                                        if trade.get("profit_loss", 0) > 0
                                        else "text-red-600"
                                    ),
                                ),
                            ],
                            className="border-b",
                        )
                        for trade in reversed(trades[-5:])  # Show last 5 trades
                    ]
                ),
            ],
            className="min-w-full table-auto",
        )

    def calculate_moving_averages(self):
        prices_list = list(self.prices)
        if len(prices_list) >= self.strategy.long_window:
            # Calculate short MA
            short_ma = np.convolve(
                prices_list,
                np.ones(self.strategy.short_window) / self.strategy.short_window,
                mode="valid",
            )
            self.short_ma.append(short_ma[-1])

            # Calculate long MA
            long_ma = np.convolve(
                prices_list,
                np.ones(self.strategy.long_window) / self.strategy.long_window,
                mode="valid",
            )
            self.long_ma.append(long_ma[-1])

            # Get trading signal
            signal = self.strategy.calculate_signals(prices_list)
            self.signals.append(signal)
            return signal
        return None

    def update_graph_and_signal(self, n):
        current_price = self.prices[-1] if self.prices else 0
        current_time = (
            self.price_times[-1] if self.price_times else int(time.time() * 1000)
        )

        # Calculate MAs and get signal
        current_signal = self.calculate_moving_averages()

        # Execute trade if we have a signal
        if current_signal:
            self.strategy.execute_trade(
                current_signal, current_price, current_time, self.investment_amount
            )

        # Get performance metrics and trade history
        metrics = self.strategy.get_performance_metrics()
        trade_history = self.strategy.get_trade_history()

        traces = []

        # Price trace
        traces.append(
            go.Scatter(
                x=list(self.price_times),
                y=list(self.prices),
                name="Price",
                mode="lines+markers",
                line=dict(color="blue"),
            )
        )

        # Add MA traces if we have enough data
        if len(self.short_ma) > 0:
            traces.append(
                go.Scatter(
                    x=list(self.price_times)[-len(self.short_ma) :],
                    y=list(self.short_ma),
                    name=f"{self.strategy.short_window}MA",
                    mode="lines",
                    line=dict(color="orange"),
                )
            )

        if len(self.long_ma) > 0:
            traces.append(
                go.Scatter(
                    x=list(self.price_times)[-len(self.long_ma) :],
                    y=list(self.long_ma),
                    name=f"{self.strategy.long_window}MA",
                    mode="lines",
                    line=dict(color="red"),
                )
            )

        # Layout
        layout = go.Layout(
            title=f"{self.symbol} Real-Time Price with Moving Averages",
            xaxis=dict(
                range=[
                    min(self.price_times) if self.price_times else 0,
                    max(self.price_times) if self.price_times else 0,
                ]
            ),
            yaxis=dict(
                range=[
                    min(
                        min(self.prices) if self.prices else 0,
                        min(self.short_ma) if self.short_ma else float("inf"),
                        min(self.long_ma) if self.long_ma else float("inf"),
                    ),
                    max(
                        max(self.prices) if self.prices else 0,
                        max(self.short_ma) if self.short_ma else 0,
                        max(self.long_ma) if self.long_ma else 0,
                    ),
                ]
            ),
        )

        # Generate signal text with current position
        signal_style = {
            "buy": {"color": "green"},
            "sell": {"color": "red"},
            None: {"color": "black"},
        }

        signal_text = html.Div(
            [
                html.P(
                    f"Current Signal: {current_signal if current_signal else 'Waiting for data...'}",
                    style=signal_style.get(current_signal, {"color": "black"}),
                ),
                html.P(f"Current Position: {metrics['position']}", className="mt-2"),
            ]
        )

        # Create metric cards and trade history table
        metric_cards = self.create_metrics_cards(metrics)
        trade_table = self.create_trade_history_table(trade_history)

        return (
            {"data": traces, "layout": layout},
            signal_text,
            metric_cards,
            trade_table,
        )

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

    def run(self):
        self.start_websocket()
        self.app.run_server(debug=True, port=8050)
