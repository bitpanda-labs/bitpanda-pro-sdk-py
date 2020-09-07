"""Stateful Websocket client keeping the state of the account orders, order book, ..."""
import json
import logging
import typing

from bpprosdk.websockets.account.account_state import AccountState
from bpprosdk.websockets.orderbook.orderbook import OrderBook
from bpprosdk.websockets.orders.cancel_order import CancelOrderByClientId, CancelOrderByOrderId
from bpprosdk.websockets.orders.create_order import CreateOrder
from bpprosdk.websockets.orders.orders_message_handler import OrdersMessageHandler
from bpprosdk.websockets.subscriptions import Subscriptions, ChannelName, AccountHistorySubscription, \
    TradingSubscription, OrdersSubscription
from bpprosdk.websockets.trading.account_history_message_handler import AccountHistoryMessageHandler
from bpprosdk.websockets.trading.trading_message_handler import TradingMessageHandler
from bpprosdk.websockets.unsubscription import Unsubscription
from bpprosdk.websockets.websocket_client import BitpandaProWebsocketClient

LOG = logging.getLogger(__name__)


class AdvancedBitpandaProWebsocketClient:
    """Advanced Websocket client"""

    def __init__(self, api_token=None, wss_host=None, callback=None):
        LOG.debug("init advanced client...")
        self.callback = callback
        self.bp_ws_client = BitpandaProWebsocketClient(api_token, wss_host, self.handle_message)
        self.order_books = dict()
        self.state = AccountState(dict(), dict(), dict(), dict(), dict(), dict(), dict())
        self.trading = TradingMessageHandler(self.state)
        self.orders_handler = OrdersMessageHandler(self.state)
        self.account_history = AccountHistoryMessageHandler(self.state)
        self.trading_buffer = []
        self.initial_state_restore = False

    async def handle_message(self, json_message: json):
        """Handles received messages by passing them to the correct components"""
        LOG.debug(">>> %s", json_message)
        await self.callback(json_message)
        if json_message["type"] == "HEARTBEAT":
            # Ignore heartbeat
            pass
        elif json_message["type"] == "ORDER_BOOK_UPDATE":
            self.order_books[json_message["instrument_code"]].update(json_message)
        elif json_message["type"] == "ORDER_BOOK_SNAPSHOT":
            self.order_books[json_message["instrument_code"]].init_with_snapshot(json_message)
        elif json_message["type"] == "SUBSCRIPTIONS":
            subscribed_channels = json_message["channels"]
            for channel in subscribed_channels:
                if channel["name"] == ChannelName.order_book.value:
                    for code in channel["instrument_codes"]:
                        LOG.debug("Adding order book store with instrument_code %s", code)
                        self.order_books.update({str(code): OrderBook()})
        elif json_message["type"] == "UNSUBSCRIBED":
            if json_message["channel_name"] == "ORDER_BOOK":
                LOG.debug("Remove order books from store due to unsubscribe")
                self.order_books = dict()
        elif json_message["channel_name"] == ChannelName.orders.value:
            self.orders_handler.handle_message(json_message)
        elif json_message["channel_name"] == ChannelName.trading.value:
            if not self.initial_state_restore:
                # Buffer events until ACTIVE_ORDERS_SNAPSHOT snapshot was consumed
                self.trading_buffer.append(json_message)
            else:
                self.trading.handle_message(json_message)
        elif json_message["channel_name"] == ChannelName.account_history.value:
            self.account_history.handle_message(json_message)
            if json_message["type"] == "ACTIVE_ORDERS_SNAPSHOT":
                self.apply_trading_buffer()
        elif json_message["type"] == "ERROR":
            LOG.error("!!! %s", json_message)

    def apply_trading_buffer(self):
        """Applies buffered trading channel message as account history snapshot can take a bit to be received"""
        for buffered_message in self.trading_buffer:
            self.trading.handle_message(buffered_message)
        self.trading_buffer.clear()
        self.initial_state_restore = True

    async def subscribe(self, subscriptions: Subscriptions):
        """Subscribes to the provided websocket channels"""
        await self.bp_ws_client.subscribe(subscriptions)

    async def close(self):
        """Closes the websocket connection"""
        await self.bp_ws_client.close()

    async def unsubscribe(self, unsubscription: Unsubscription):
        """Unsubscribe from websocket channel(s)"""
        await self.bp_ws_client.unsubscribe(unsubscription)

    async def create_order(self, order: CreateOrder):
        """Creates an order via orders channel"""
        await self.bp_ws_client.create_order(order)

    async def cancel_order(self, cancel: typing.Union[CancelOrderByOrderId, CancelOrderByClientId]):
        """Cancels an order via orders channel"""
        await self.bp_ws_client.cancel_order(cancel)

    async def send_message(self, message: json):
        """Sends a message to the open websocket connection"""
        await self.bp_ws_client.send_message(message)

    def get_order_book(self, instrument_code: str):
        """Returns a order book by instrument_code"""
        return self.order_books[instrument_code]

    def get_order_books(self):
        """Returns all available order books"""
        return self.order_books

    def get_state(self):
        """Returns account store"""
        return self.state

    async def start(self, subscriptions: Subscriptions):
        """Start websocket connection and enables store"""
        await self.start_with(subscriptions, True)

    async def start_with(self, subscriptions: Subscriptions, use_store: bool):
        """Start websocket connection"""
        LOG.debug("creating a new connection...")
        if use_store:
            if subscriptions is None:
                subscriptions = Subscriptions([])
            # Add subscription to ACCOUNT_HISTORY, TRADING & ORDERS channel when using the store
            subscriptions.add_subscription(AccountHistorySubscription())
            subscriptions.add_subscription(TradingSubscription())
            subscriptions.add_subscription(OrdersSubscription())
            LOG.info("Account state management activated!")
        else:
            LOG.info("No account state management as ACCOUNT_HISTORY, TRADING & ORDERS channel not found!")
        await self.bp_ws_client.start(subscriptions)
