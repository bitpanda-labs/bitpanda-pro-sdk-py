# pylint: skip-file
import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import List


class ChannelName(Enum):
    order_book = "ORDER_BOOK"
    trading = "TRADING"
    orders = "ORDERS"
    account_history = "ACCOUNT_HISTORY"


class Subscription(ABC):

    @abstractmethod
    def get_message(self) -> json:
        pass


class OrderBookSubscription(Subscription):

    def __init__(self, instrument_codes=None, depth=10):
        super().__init__()
        self.instrument_codes = instrument_codes
        self.depth = depth

    def get_message(self):
        return {
            "name": ChannelName.order_book.value,
            "depth": self.depth,
            "instrument_codes": self.instrument_codes
        }


class AccountHistorySubscription(Subscription):

    def __init__(self, just_orders=False):
        super().__init__()
        self.just_orders = just_orders

    def get_message(self):
        return {
            "name": ChannelName.account_history.value
        }


class TradingSubscription(Subscription):

    def __init__(self):
        super().__init__()

    def get_message(self):
        return {
            "name": ChannelName.trading.value
        }


class OrdersSubscription(Subscription):

    def __init__(self):
        super().__init__()

    def get_message(self):
        return {
            "name": ChannelName.orders.value
        }


class Subscriptions:

    def __init__(self, channel_subscriptions: List[Subscription] = None):
        self.channel_subscriptions = channel_subscriptions

    def as_json(self):
        channels = [s.get_message() for s in self.channel_subscriptions]
        return json.dumps({
            "type": "SUBSCRIBE",
            "channels": channels
        })

    def add_subscription(self, subscription: Subscription):
        if subscription not in self.channel_subscriptions:
            self.channel_subscriptions.append(subscription)
