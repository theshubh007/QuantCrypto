import websocket
import json
import threading
import time
from collections import deque
import logging
from threading import Event
from logging.handlers import RotatingFileHandler
import gc
import psutil
import numpy as np
from datetime import datetime


class EnhancedCryptoStream:
    def __init__(self, symbol="BTC-USD", max_retries=5, retry_delay=5):
        # Set up logging first
        logging.basicConfig(
            level=logging.WARNING,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                RotatingFileHandler(
                    "crypto_stream.log",
                    maxBytes=1024 * 1024,
                    backupCount=2,
                )
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Basic configuration
        self.symbol = symbol
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_count = 0

        # Memory management configuration
        self.memory_threshold = 85  # Memory usage threshold (%)
        self.last_memory_check = time.time()
        self.memory_check_interval = 60  # Check memory every 60 seconds
        self.cleanup_interval = 300  # Cleanup every 5 minutes
        self.last_cleanup = time.time()

        # Data aggregation settings
        self.price_buffer = []
        self.buffer_size = 10
        self.last_aggregate = time.time()
        self.aggregate_interval = 1  # Aggregate every second

        # Connection management
        self.ws = None
        self.connected = Event()
        self.should_reconnect = True

        # Initialize Basic monitoring
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 30  # 30 seconds

        # Now adjust buffer sizes after logger is initialized
        self.adjust_buffer_sizes()

    def adjust_buffer_sizes(self):
        """Dynamically adjust buffer sizes based on available system memory"""
        try:
            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024 * 1024)
            buffer_size = min(200, max(50, int(available_mb / 10)))

            # Initialize data storage with adjusted size
            self.price_times = deque(maxlen=buffer_size)
            self.prices = deque(maxlen=buffer_size)

            self.logger.info(f"Buffer size adjusted to {buffer_size}")
        except Exception as e:
            self.logger.error(f"Error adjusting buffer sizes: {str(e)}")
            # Fallback to default sizes
            self.price_times = deque(maxlen=200)
            self.prices = deque(maxlen=200)

    def check_memory_usage(self):
        """Monitor and manage memory usage"""
        current_time = time.time()
        if current_time - self.last_memory_check >= self.memory_check_interval:
            try:
                memory = psutil.virtual_memory()
                if memory.percent > self.memory_threshold:
                    self.logger.warning(f"High memory usage: {memory.percent}%")
                    self.perform_emergency_cleanup()
                self.last_memory_check = current_time
            except Exception as e:
                self.logger.error(f"Memory check error: {str(e)}")

    def perform_emergency_cleanup(self):
        """Emergency cleanup when memory usage is high"""
        try:
            gc.collect()
            # Reduce buffer sizes
            new_size = int(len(self.prices) * 0.7)
            self.prices = deque(
                list(self.prices)[-new_size:], maxlen=self.prices.maxlen
            )
            self.price_times = deque(
                list(self.price_times)[-new_size:], maxlen=self.price_times.maxlen
            )
            self.price_buffer = []
            self.logger.info("Emergency cleanup completed")
        except Exception as e:
            self.logger.error(f"Emergency cleanup error: {str(e)}")

    def cleanup_old_data(self):
        """Periodic cleanup of old data"""
        current_time = time.time()
        if current_time - self.last_cleanup >= self.cleanup_interval:
            try:
                gc.collect()
                if len(self.prices) > self.prices.maxlen * 0.8:
                    retain_size = int(self.prices.maxlen * 0.7)
                    self.prices = deque(
                        list(self.prices)[-retain_size:], maxlen=self.prices.maxlen
                    )
                    self.price_times = deque(
                        list(self.price_times)[-retain_size:],
                        maxlen=self.price_times.maxlen,
                    )
                self.last_cleanup = current_time
            except Exception as e:
                self.logger.error(f"Cleanup error: {str(e)}")

    def aggregate_data(self):
        """Aggregate buffered price data"""
        if not self.price_buffer:
            return
        try:
            avg_price = float(np.mean(self.price_buffer))
            current_time = int(time.time() * 1000)
            self.prices.append(avg_price)
            self.price_times.append(current_time)
            self.price_buffer = []
        except Exception as e:
            self.logger.error(f"Aggregation error: {str(e)}")

    def handle_connection_error(self):
        """Handle connection errors with exponential backoff"""
        if self.retry_count < self.max_retries:
            wait_time = self.retry_delay * (2**self.retry_count)
            self.logger.warning(
                f"Connection retry {self.retry_count + 1}/{self.max_retries}"
            )
            time.sleep(wait_time)
            self.retry_count += 1
            return True
        else:
            self.logger.error("Max retries reached")
            return False

    def check_connection_health(self):
        """Monitor connection health and memory"""
        while self.should_reconnect:
            time.sleep(5)
            current_time = time.time()

            # Check heartbeat
            if current_time - self.last_heartbeat > self.heartbeat_interval * 2:
                self.logger.warning("Heartbeat timeout")
                self.reconnect()

            # Memory management
            self.check_memory_usage()
            self.cleanup_old_data()

    def on_message(self, ws, message):
        """Handle incoming messages with memory management"""
        try:
            data = json.loads(message)
            if data.get("type") == "ticker" and data.get("product_id") == self.symbol:
                price = float(data.get("price", 0))
                self.price_buffer.append(price)

                current_time = time.time()
                if (
                    len(self.price_buffer) >= self.buffer_size
                    or current_time - self.last_aggregate >= self.aggregate_interval
                ):
                    self.aggregate_data()
                    self.last_aggregate = current_time

                # Log significant price changes
                if len(self.prices) > 1:
                    price_change = (
                        abs(self.prices[-1] - self.prices[-2]) / self.prices[-2] * 100
                    )
                    if price_change > 1:
                        self.logger.info(f"Price change: {price_change:.2f}%")

            elif data.get("type") == "heartbeat":
                self.last_heartbeat = time.time()

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Processing error: {str(e)}")

    # [Previous methods remain unchanged]
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        self.logger.error("WebSocket error")
        if not self.connected.is_set():
            self.reconnect()

    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket closure"""
        self.logger.warning("WebSocket closed")
        self.connected.clear()
        if self.should_reconnect:
            self.reconnect()

    def on_open(self, ws):
        """Handle WebSocket connection opening"""
        self.logger.info("WebSocket opened")
        self.connected.set()
        self.retry_count = 0

        subscribe_message = {
            "type": "subscribe",
            "product_ids": [self.symbol],
            "channels": ["ticker", "heartbeat"],
        }
        ws.send(json.dumps(subscribe_message))

    def reconnect(self):
        """Handle reconnection logic"""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass

        self.connected.clear()
        if self.handle_connection_error():
            self.start_websocket()

    def start_websocket(self):
        """Initialize WebSocket connection"""
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            "wss://ws-feed.exchange.coinbase.com",
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )

        health_thread = threading.Thread(target=self.check_connection_health)
        health_thread.daemon = True
        health_thread.start()

        self.ws.run_forever(ping_interval=30, ping_timeout=10)

    def stop(self):
        """Graceful shutdown"""
        self.should_reconnect = False
        if self.ws:
            self.ws.close()
        self.logger.info("Stream stopped")

    def get_current_price(self):
        """Safe method to get current price"""
        return self.prices[-1] if self.prices else None

    def get_price_history(self):
        """Safe method to get price history"""
        return list(self.prices)
