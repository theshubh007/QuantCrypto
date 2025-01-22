import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from collections import deque
import json
import threading
import time
import numpy as np
from datetime import datetime
from src.Strategies.moving_average import MovingAverageStrategy
from src.Data_feed.DataStream import EnhancedCryptoStream
import os


class CryptoPriceDashboard2:
    def __init__(
        self, symbol="BTC-USD", short_window=10, long_window=50, investment_amount=1000
    ):
        # Initialize price and time tracking (these will now be managed by EnhancedCryptoStream)
        self.investment_amount = investment_amount

        # Initialize strategy
        self.strategy = MovingAverageStrategy(short_window, long_window)
        self.short_ma = deque(maxlen=200)
        self.long_ma = deque(maxlen=200)
        self.signals = deque(maxlen=200)

        # Initialize the enhanced crypto stream
        self.crypto_stream = EnhancedCryptoStream(symbol=symbol)

        # Store symbol for reference
        self.symbol = symbol

        # Dash app setup with proper asset serving
        self.app = dash.Dash(
            __name__,
            assets_folder="assets",
            external_stylesheets=[
                "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
            ],
            suppress_callback_exceptions=True,
        )
        print(f"Assets folder path: {self.app.config.assets_folder}")
        # Main layout with proper styling classes
        # Main layout with proper styling classes
        self.app.layout = html.Div(
            [
                # Header Section with text-based link
                html.Div(
                    [
                        html.Div(
                            [
                                # Left side - Title
                                html.H1(
                                    "BTC-USD Trading Terminal | Real-Time Analysis & Automated Signals",
                                    className="header-title",
                                ),
                                # Right side - Developer Info
                                html.Div(
                                    [
                                        "Developed by ",
                                        html.A(
                                            "Shubham Kothiya | LinkedIn →",
                                            href="https://www.linkedin.com/in/shubham-kothiya/",
                                            target="_blank",
                                            className="developer-link",
                                        ),
                                    ],
                                    className="developer-info",
                                ),
                            ],
                            className="header-container",
                        ),
                    ],
                    className="dashboard-container",
                ),
                # Main Chart - Moved here, right after header
                html.Div(
                    dcc.Graph(
                        id="live-graph", animate=True, className="chart-container"
                    ),
                    className="bg-dark rounded-lg shadow-lg p-4 mb-4",
                ),
                # Account Metrics Section
                html.Div(
                    id="account-metrics",
                    className="metrics-grid animate-fade-in",
                ),
                # Trading Signals and Performance
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "Current Trading Signal",
                                    className="text-xl font-bold mb-2 text-white",
                                ),
                                html.Div(
                                    id="signal-output", className="signal-container"
                                ),
                            ],
                            className="metric-card",
                        ),
                        html.Div(
                            [
                                html.H3(
                                    "Recent Trades",
                                    className="text-xl font-bold mb-2 text-white",
                                ),
                                html.Div(
                                    id="trade-history",
                                    className="trade-history-container",
                                ),
                            ],
                            className="metric-card",
                        ),
                    ],
                    className="grid grid-cols-1 gap-4",
                ),
                dcc.Interval(id="graph-update", interval=1000, n_intervals=0),
            ],
            className="min-h-screen bg-dark",
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
        """Create metric cards for account overview with optimized layout"""
        return html.Div(
            [
                # Top row with metrics and strategy
                html.Div(
                    [
                        # Balance Card
                        html.Div(
                            [
                                html.H4("CURRENT BALANCE", className="metric-label"),
                                html.P(
                                    self.format_currency(metrics["current_balance"]),
                                    className="metric-value",
                                ),
                                html.P(
                                    f"{metrics['return_percentage']}% Return",
                                    className=f"{'value-positive' if metrics['return_percentage'] >= 0 else 'value-negative'}",
                                ),
                            ],
                            className="metric-card",
                        ),
                        # P&L Card
                        html.Div(
                            [
                                html.H4("TOTAL P&L", className="metric-label"),
                                html.P(
                                    self.format_currency(metrics["total_profit_loss"]),
                                    className=f"metric-value {'value-positive' if metrics['total_profit_loss'] >= 0 else 'value-negative'}",
                                ),
                            ],
                            className="metric-card",
                        ),
                        # Win Rate Card
                        html.Div(
                            [
                                html.H4("WIN RATE", className="metric-label"),
                                html.P(
                                    f"{metrics.get('win_rate', 0)}%",
                                    className="metric-value",
                                ),
                            ],
                            className="metric-card",
                        ),
                        # Strategy Card (taking remaining space)
                        html.Div(
                            [
                                html.H4(
                                    "Moving Average Strategy",
                                    className="strategy-title",
                                ),
                                html.P(
                                    "This trading system utilizes Moving Average Crossover strategy, combining short-term and long-term market trends for signal generation.",
                                    className="strategy-description",
                                ),
                                html.Div(
                                    [
                                        html.H5(
                                            "Signal Generation",
                                            className="feature-title",
                                        ),
                                        html.P(
                                            "Golden Cross (buy) and Death Cross (sell)"
                                        ),
                                    ],
                                    className="strategy-feature",
                                ),
                            ],
                            className="strategy-card",
                        ),
                    ],
                    className="metrics-grid",
                ),
                # Bottom row with MA cards
                html.Div(
                    [
                        # Short MA Card
                        html.Div(
                            [
                                html.H4(
                                    f"{self.strategy.short_window}MA",
                                    className="ma-title",
                                ),
                                html.Ul(
                                    [
                                        html.Li("Quick price changes"),
                                        html.Li("Short-term momentum"),
                                        html.Li("Rapid market moves"),
                                    ],
                                    className="ma-list",
                                ),
                            ],
                            className="ma-card",
                        ),
                        # Long MA Card
                        html.Div(
                            [
                                html.H4(
                                    f"{self.strategy.long_window}MA",
                                    className="ma-title",
                                ),
                                html.Ul(
                                    [
                                        html.Li("Market direction"),
                                        html.Li("Reduced noise"),
                                        html.Li("Trend confirmation"),
                                    ],
                                    className="ma-list",
                                ),
                            ],
                            className="ma-card",
                        ),
                    ],
                    className="ma-indicators",
                ),
            ]
        )

    def create_trade_history_table(self, trades):
        """Create trade history table with fees and tax information"""
        if not trades:
            return html.P("No trades yet", className="text-white")

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
                            html.Th("Fee", className="p-2"),  # New column
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
                                # Time
                                html.Td(
                                    datetime.fromtimestamp(
                                        trade["timestamp"] / 1000
                                    ).strftime("%H:%M:%S"),
                                    className="p-2",
                                ),
                                # Type (Buy/Sell)
                                html.Td(
                                    trade["type"].upper(),
                                    className="p-2 font-bold "
                                    + (
                                        "text-green-600"
                                        if trade["type"] == "buy"
                                        else "text-red-600"
                                    ),
                                ),
                                # Price
                                html.Td(
                                    self.format_currency(trade["price"]),
                                    className="p-2",
                                ),
                                # Amount
                                html.Td(
                                    f"{trade['coins']:.8f}",
                                    className="p-2",
                                ),
                                # Fee
                                html.Td(
                                    self.format_currency(trade["fee"]),
                                    className="p-2 text-yellow-400",  # Highlight fees
                                ),
                                # Tax (only for sell trades)
                                html.Td(
                                    (
                                        self.format_currency(trade.get("tax", 0))
                                        if "tax" in trade
                                        else "-"
                                    ),
                                    className="p-2 text-yellow-400",  # Highlight taxes
                                ),
                                # P&L
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
                            className="border-b border-gray-700",  # Darker border for theme consistency
                        )
                        for trade in reversed(trades[-5:])  # Show last 5 trades
                    ]
                ),
            ],
            className="min-w-full table-auto bg-gray-800 rounded-lg overflow-hidden",  # Enhanced table styling
        )

    def calculate_moving_averages(self):
        """Calculate moving averages using data from EnhancedCryptoStream"""
        # Get prices from the crypto stream
        prices_list = list(self.crypto_stream.prices)

        if len(prices_list) >= self.strategy.long_window:
            try:
                # Calculate short MA with numpy for efficiency
                short_window_vals = prices_list[-self.strategy.short_window :]
                short_ma_value = np.mean(short_window_vals)
                self.short_ma.append(short_ma_value)

                # Calculate long MA with numpy for efficiency
                long_window_vals = prices_list[-self.strategy.long_window :]
                long_ma_value = np.mean(long_window_vals)
                self.long_ma.append(long_ma_value)

                # Get trading signal
                signal = self.strategy.calculate_signals(prices_list)
                self.signals.append(signal)
                return signal

            except Exception as e:
                print(f"Error calculating moving averages: {str(e)}")
                return None
        return None

    def update_graph_and_signal(self, n):
        """Update the dashboard with latest data from EnhancedCryptoStream"""
        try:
            # Get current price and time from crypto stream
            current_price = (
                self.crypto_stream.prices[-1]
                if len(self.crypto_stream.prices) > 0
                else 0
            )
            current_time = (
                self.crypto_stream.price_times[-1]
                if len(self.crypto_stream.price_times) > 0
                else int(time.time() * 1000)
            )

            # Calculate MAs and get signal
            current_signal = self.calculate_moving_averages()

            # Execute trade if we have a valid signal
            if current_signal and current_price > 0:
                self.strategy.execute_trade(
                    current_signal, current_price, current_time, self.investment_amount
                )

            # Get performance metrics and trade history
            metrics = self.strategy.get_performance_metrics()
            trade_history = self.strategy.get_trade_history()

            # NEW CODE:
            formatted_times = [
                datetime.fromtimestamp(t / 1000) for t in self.crypto_stream.price_times
            ]
            traces = [
                go.Scatter(
                    x=formatted_times,  # Using formatted datetime objects
                    y=list(self.crypto_stream.prices),
                    name="Price",
                    mode="lines+markers",
                    line=dict(color="#3b82f6"),
                    marker=dict(size=4),
                )
            ]

            # For Short MA
            if len(self.short_ma) > 0:
                # Calculate correct x-axis values for MAs
                ma_times = list(self.crypto_stream.price_times)[-len(self.short_ma) :]
                formatted_ma_times = [
                    datetime.fromtimestamp(t / 1000) for t in ma_times
                ]
                traces.append(
                    go.Scatter(
                        x=formatted_ma_times,  # Using formatted datetime objects
                        y=list(self.short_ma),
                        name=f"{self.strategy.short_window}MA",
                        mode="lines",
                        line=dict(color="#f59e0b"),
                    )
                )

            # For Long MA
            if len(self.long_ma) > 0:
                ma_times = list(self.crypto_stream.price_times)[-len(self.long_ma) :]
                formatted_ma_times = [
                    datetime.fromtimestamp(t / 1000) for t in ma_times
                ]
                traces.append(
                    go.Scatter(
                        x=formatted_ma_times,  # Using formatted datetime objects
                        y=list(self.long_ma),
                        name=f"{self.strategy.long_window}MA",
                        mode="lines",
                        line=dict(color="#ef4444"),
                    )
                )

            layout = go.Layout(
                title=f"{self.symbol} Real-Time Price with Moving Averages",
                paper_bgcolor="#1c2537",
                plot_bgcolor="#1c2537",
                font=dict(color="#e2e8f0"),
                xaxis=dict(
                    range=[
                        min(formatted_times) if formatted_times else 0,
                        max(formatted_times) if formatted_times else 0,
                    ],
                    gridcolor="#2d3748",
                    zerolinecolor="#2d3748",
                    type="date",  # Specify x-axis type as date
                    tickformat="%H:%M:%S",  # Format as Hours:Minutes:Seconds
                    tickmode="auto",  # Automatic tick mode
                    nticks=10,  # Number of ticks to display
                    tickfont=dict(size=10),  # Tick font size
                ),
                yaxis=dict(
                    range=self._calculate_y_axis_range(),
                    gridcolor="#2d3748",
                    zerolinecolor="#2d3748",
                ),
            )

            # Generate signal components
            signal_text = self._generate_signal_text(current_signal, metrics)
            metric_cards = self.create_metrics_cards(metrics)
            trade_table = self.create_trade_history_table(trade_history)

            return (
                {"data": traces, "layout": layout},
                signal_text,
                metric_cards,
                trade_table,
            )

        except Exception as e:
            print(f"Error updating dashboard: {str(e)}")
            # Return empty/default values in case of error
            return self._generate_empty_dashboard()

    def _calculate_y_axis_range(self):
        """Calculate dynamic y-axis range for the graph"""
        try:
            min_price = (
                min(self.crypto_stream.prices) if self.crypto_stream.prices else 0
            )
            max_price = (
                max(self.crypto_stream.prices) if self.crypto_stream.prices else 0
            )

            # Include MA values in range calculation
            if self.short_ma:
                min_price = min(min_price, min(self.short_ma))
                max_price = max(max_price, max(self.short_ma))
            if self.long_ma:
                min_price = min(min_price, min(self.long_ma))
                max_price = max(max_price, max(self.long_ma))

            # Add padding
            padding = (max_price - min_price) * 0.05
            return [min_price - padding, max_price + padding]
        except Exception as e:
            print(f"Error calculating y-axis range: {str(e)}")
            return [0, 100]  # Default range

    def _generate_empty_dashboard(self):
        """Generate empty dashboard components for error cases"""
        empty_figure = {
            "data": [],
            "layout": go.Layout(
                title="Waiting for data...",
                paper_bgcolor="#1c2537",
                plot_bgcolor="#1c2537",
                font=dict(color="#e2e8f0"),
            ),
        }

        empty_signal = html.Div("No signal available", className="signal-container")

        empty_metrics = self.create_metrics_cards(
            {
                "current_balance": 0,
                "total_profit_loss": 0,
                "return_percentage": 0,
                "win_rate": 0,
                "position": "None",
            }
        )

        empty_history = self.create_trade_history_table([])

        return empty_figure, empty_signal, empty_metrics, empty_history

    def _generate_signal_text(self, current_signal, metrics):
        """Generate signal text component with current position"""
        signal_style = {
            "buy": {"color": "#10b981"},  # Green
            "sell": {"color": "#ef4444"},  # Red
            None: {"color": "#94a3b8"},  # Gray
        }

        return html.Div(
            [
                html.P(
                    f"Current Signal: {current_signal if current_signal else 'Waiting for data...'}",
                    style=signal_style.get(current_signal, {"color": "#94a3b8"}),
                    className="text-lg",
                ),
                html.P(
                    f"Current Position: {metrics['position']}",
                    className="mt-2 text-white",
                ),
            ],
            className="signal-container",
        )

    def stop_stream(self):
        """Gracefully shutdown the crypto stream and cleanup resources"""
        try:
            if hasattr(self, "crypto_stream"):
                print("Stopping crypto stream...")
                self.crypto_stream.stop()

                # Wait for websocket thread to finish
                if hasattr(self, "websocket_thread") and self.websocket_thread:
                    self.websocket_thread.join(timeout=5)

                # Save final state
                self._save_final_state()

            print("Stream stopped successfully")

        except Exception as e:
            print(f"Error stopping stream: {str(e)}")

    def _save_final_state(self):
        """Save the final state before shutdown"""
        if not self.crypto_stream.prices:
            return

        try:
            final_state = {
                "timestamp": time.time(),
                "last_price": self.crypto_stream.prices[-1],
                "metrics": self.strategy.get_performance_metrics(),
                "trade_history": self.strategy.get_trade_history(),
            }

            with open("dashboard_state.json", "w") as f:
                json.dump(final_state, f)

        except Exception as e:
            print(f"Error saving final state: {str(e)}")

    def start_websocket(self):
        """Start the websocket connection using EnhancedCryptoStream"""
        try:
            # Create a thread for the crypto stream
            self.websocket_thread = threading.Thread(
                target=self.crypto_stream.start_websocket
            )
            self.websocket_thread.daemon = True
            self.websocket_thread.start()

            # Wait for initial connection
            timeout = 10  # seconds
            start_time = time.time()
            while not self.crypto_stream.connected.is_set():
                if time.time() - start_time > timeout:
                    raise TimeoutError("Failed to establish WebSocket connection")
                time.sleep(0.1)

            print("WebSocket connection established successfully")

        except Exception as e:
            print(f"Error starting websocket: {str(e)}")
            raise

    def run(self):
        """Run the dashboard application with enhanced stream management"""
        try:
            # Start the websocket connection
            self.start_websocket()

            # Register shutdown handler
            import atexit

            atexit.register(self.stop_stream)

            # Monitor stream health in a separate thread
            def monitor_stream():
                while True:
                    if not self.crypto_stream.connected.is_set():
                        print("Stream connection lost, attempting to reconnect...")
                        self.start_websocket()
                    time.sleep(30)  # Check every 30 seconds

            monitor_thread = threading.Thread(target=monitor_stream)
            monitor_thread.daemon = True
            monitor_thread.start()

            # Run the Dash server
            port = int(os.environ.get("PORT", 8050))
            self.app.run_server(
                host="0.0.0.0",
                port=port,
                debug=False,
                use_reloader=False,  # Prevent duplicate streams
            )

        except Exception as e:
            print(f"Error running dashboard: {str(e)}")
            self.stop_stream()
            raise
