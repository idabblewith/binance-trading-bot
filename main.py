import tkinter as tk
import logging
import connectors.binance_futures as binance_futures
from dotenv import dotenv_values

env = dotenv_values(".env")


# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s | %(levelname)s :: %(message)s")
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)

# Set a logger file
file_handler = logging.FileHandler("info.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# Add handlers to the logger
logger.addHandler(stream_handler)
logger.addHandler(file_handler)


# Test Logs
logger.debug("Debug Log")
logger.info("Info Log")
logger.warning("Warning Log")
logger.error("Error Log")
logger.critical("Critical Log")

if __name__ == "__main__":

    FUTURES_CLIENT = binance_futures.BinanceFuturesClient(
        env=env,
        testnet=True,
    )
    contracts = FUTURES_CLIENT.get_contracts()
    FUTURES_CLIENT.check_time_difference()
    print("BALANCES: ", FUTURES_CLIENT.get_balances())
    FUTURES_CLIENT.place_order(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.01,
        type="LIMIT",
        price=30000,
        tif="GTC",
    )
    print("BALANCES: ", FUTURES_CLIENT.get_balances())
    # print(FUTURES_CLIENT.get_open_orders(symbol="BTCUSDT", order_id=1, ))
    # print(FUTURES_CLIENT.cancel_order(symbol="BTCUSDT", order_id=1, ))

    # print(
    #     FUTURES_CLIENT.get_historical_candles(
    #         symbol="BTCUSDT",
    #         interval="1h",
    #     )
    # )
    # print(FUTURES_CLIENT.get_bid_ask("BTCUSDT"))

    root = tk.Tk()
    root.configure(bg="gray12")
    root.title("Trading Bot")

    i = 0  # Column counter
    j = 0  # Row counter
    font = ("Calibri", 12, "normal")

    for contract in contracts:
        label_widget = tk.Label(
            root,
            text=contract,
            bg="gray12",
            fg="SteelBlue1",
            # borderwidth=1,
            # relief="solid",
            width=20,
            font=font,
        )
        label_widget.grid(row=j, column=i, sticky="nsew")

        i += 1
        if i == 4:  # Once 4 columns are reached, move to the next row
            i = 0
            j += 1

    root.mainloop()
