from calendar import c
import logging
from urllib.parse import urlencode
import requests
from pprint import pprint
import time

import hmac, hashlib

logger = logging.getLogger()

# "https://fapi.binance.com"
# "https://testnet.binancefuture.com"
# "wss://fstream.binance.com/ws"


class BinanceFuturesClient:
    # region Initialization & Config ========================================
    def __init__(self, testnet, env):
        if testnet:
            self.base_url = "https://testnet.binancefuture.com/"
            self.public_key = env["TESTNET_API_KEY"]
            self.secret_key = env["TESTNET_SECRET_KEY"]
        else:
            self.base_url = "https://fapi.binance.com/"
            self.public_key = env["MAINNET_API_KEY"]
            self.secret_key = env["MAINNET_SECRET_KEY"]

        self.headers = {
            "X-MBX-APIKEY": self.public_key,
        }
        self.prices = dict()
        self.time_difference = None

        logger.info("Binance Futures Client Created")

    def get_server_time(self):
        """Fetch the current server time from Binance."""
        response = self.make_request("GET", "/fapi/v1/time")
        if response:
            return response["serverTime"]
        return None

    def check_time_difference(self):
        """Calculates the time difference between local and server time."""
        server_time = self.get_server_time()
        local_time = int(time.time() * 1000)
        if server_time:
            self.time_difference = server_time - local_time
            pprint(
                {
                    "server_time": server_time,
                    "local_time": local_time,
                    "difference": f"{int(self.time_difference)}ms",
                }
            )
        else:
            logger.error("Failed to fetch server time.")

    def make_request(self, method, endpoint, params=None):
        if method == "GET":
            res = requests.get(
                f"{self.base_url}{endpoint}", params=params, headers=self.headers
            )

        elif method == "POST":
            res = requests.post(
                f"{self.base_url}{endpoint}", data=params, headers=self.headers
            )

        elif method == "DELETE":
            res = requests.delete(
                f"{self.base_url}{endpoint}", data=params, headers=self.headers
            )
        else:
            raise ValueError("Method not supported")

        if res.status_code == 200:
            return res.json()
        else:
            logger.error(
                f"{method.capitalize()} Request to {endpoint} failed with status code {res.status_code}: {res.json()}"
            )
            return None

    # endregion

    # region Market Data ========================================
    def get_contracts(self):
        exchange_info = self.make_request("GET", "fapi/v1/exchangeInfo")
        contracts = dict()
        if exchange_info != None:
            for contract_data in exchange_info["symbols"]:
                contracts[contract_data["pair"]] = contract_data
                # logger.info(pprint(contract))
        return contracts

    def get_historical_candles(self, symbol, interval):
        data = dict()
        data["symbol"] = symbol
        data["interval"] = interval
        data["limit"] = 1000

        raw_candles = self.make_request("GET", "fapi/v1/klines", data)
        candles = []
        if raw_candles is not None:
            for c in raw_candles:
                candles.append(
                    {
                        "time": c[0],
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4]),
                        "volume": float(c[5]),
                    }
                )
        return candles

    def get_bid_ask(self, symbol):
        data = dict()
        data["symbol"] = symbol
        ob_data = self.make_request("GET", "fapi/v1/ticker/bookTicker", data)

        if ob_data is not None:
            if symbol not in self.prices:
                self.prices[symbol] = {
                    "bid": float(ob_data["bidPrice"]),
                    "ask": float(ob_data["askPrice"]),
                }
            else:
                self.price[symbol]["bid"] = float(ob_data["bidPrice"])
                self.price[symbol]["ask"] = float(ob_data["askPrice"])

        return self.prices[symbol]

    # endregion

    # region Account Data ========================================
    def generate_signature(self, data):
        return hmac.new(
            self.secret_key.encode(), urlencode(data).encode(), hashlib.sha256
        ).hexdigest()

    def get_balances(self):
        data = dict()
        if self.time_difference is None:
            # Check the time difference if not already calculated
            self.check_time_difference()

        data["timestamp"] = int(time.time() * 1000) + self.time_difference
        data["signature"] = self.generate_signature(data)

        balances = dict()

        account_data = self.make_request("GET", "fapi/v3/account", data)

        if account_data is not None:
            # pprint(account_data)
            for a in account_data["assets"]:
                if (float(a["availableBalance"]) > 0) or (
                    float(a["walletBalance"]) > 0
                ):
                    balances[a["asset"]] = {
                        "free": float(a["availableBalance"]),
                        "locked": float(a["walletBalance"]),
                    }

        return balances

    # endregion

    # region Order Management ========================================
    def get_open_order_status(self, order_id, symbol):
        data = dict()
        data["timestamp"] = int(time.time() * 1000) + self.time_difference
        data["signature"] = self.generate_signature(data)
        data["orderId"] = order_id
        data["symbol"] = symbol

        order_status = self.make_request("GET", "fapi/v1/order", data)
        return order_status

    def place_order(self, symbol, side, quantity, type, price=None, tif=None):
        data = dict()
        data["symbol"] = symbol
        data["side"] = side
        data["type"] = type
        data["quantity"] = quantity

        if price is not None:
            data["price"] = price
        if tif is not None:
            data["timeInForce"] = tif

        data["timestamp"] = int(time.time() * 1000) + self.time_difference
        data["signature"] = self.generate_signature(data)

        order_status = self.make_request("POST", "fapi/v1/order", data)
        if order_status is not None:
            logger.info(f"Order placed successfully: {order_status}")
        else:
            logger.error(f"Failed to place order: {order_status}")
        return order_status

    def cancel_order(self, symbol, order_id):
        data = dict()
        data["symbol"] = symbol
        data["orderId"] = order_id

        data["timestamp"] = int(time.time() * 1000) + self.time_difference
        data["signature"] = self.generate_signature(data)

        order_status = self.make_request("DELETE", "fapi/v1/order", data)
        return order_status

    # endregion
