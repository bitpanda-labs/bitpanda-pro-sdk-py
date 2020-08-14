"""Order Book model"""
import json

from decimal import Decimal


class OrderBook:
    """Stores the state of the order book"""

    def __init__(self):
        self.asks = dict()
        self.bids = dict()
        self.instrument_code = None

    def get_bids(self):
        """
        All bids of the order book
        """
        return self.bids

    def get_asks(self):
        """
        All asks of the order book
        """
        return self.asks

    def init_with_snapshot(self, json_data: json):
        """
        Initialize order book with snapshot. Previous data is discarded.
        """
        self.instrument_code = json_data["instrument_code"]
        # discard old data
        self.asks = dict()
        self.bids = dict()

        for price, amount in json_data["asks"]:
            self.asks.update({price: amount})

        for price, amount in json_data["bids"]:
            self.bids.update({price: amount})

    def update(self, json_update: json):
        """
        Updates bids + asks of order book
        """
        changes = json_update["changes"]
        for side, price, amount in changes:
            if side == "BUY":
                if Decimal(amount) > Decimal(0):
                    # add bid
                    self.bids.update({price: amount})
                elif Decimal(amount) <= Decimal(0):
                    # remove bid
                    if self.bids.get(price) is not None:
                        self.bids.pop(price)
            elif side == "SELL":
                if Decimal(amount) > Decimal(0):
                    # add ask
                    self.asks.update({price: amount})
                elif Decimal(amount) <= Decimal(0):
                    # remove ask
                    if self.asks.get(price) is not None:
                        self.asks.pop(price)
