from src.app.Adv_Dashboard import CryptoPriceDashboard2
import os


def main():
    # Initialize dashboard with default settings
    dashboard = CryptoPriceDashboard2(
        symbol="BTC-USD", short_window=10, long_window=50, investment_amount=1000
    )

    # Run the dashboard
    try:
        dashboard.run()
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Cleanup if needed
        pass


if __name__ == "__main__":
    main()
