"""Handles all messages coming from trading channel"""
# pylint: disable=no-member
import json
import logging

from bpprosdk.websockets.account.account_state import AccountState
from bpprosdk.websockets.trading.trading_channel_events import Fill, Booked, Done, Tracked, Triggered

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler())


class TradingMessageHandler:
    """Handles trading channel messages"""

    def __init__(self, state: AccountState = None):
        self.state = state

    def handle_message(self, json_message: json):
        """Updates the state depending on the received message"""
        message = json.dumps(json_message)
        if json_message["type"] == "BOOKED":
            booked = Booked.from_json(message)
            self.state.update_open_orders(booked)
        elif json_message["type"] == "FILL":
            fill = Fill.from_json(message)
            self.state.fill_open_order(fill)
        elif json_message["type"] == "DONE":
            done = Done.from_json(message)
            self.state.order_done(done)
        elif json_message["type"] == "TRACKED":
            tracked = Tracked.from_json(message)
            LOG.debug("Stop Order tracked: %s", tracked)
            self.state.update_open_orders_on_stop_order(tracked)
        elif json_message["type"] == "TRIGGERED":
            triggered = Triggered.from_json(message)
            LOG.debug("Stop Order triggered %s", triggered)
        else:
            LOG.warning("Unhandled event from TRADING channel %s", message)
