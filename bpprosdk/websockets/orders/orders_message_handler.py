"""Handles all messages coming from trading channel"""
import json
import logging

from bpprosdk.websockets.account.account_state import AccountState
from bpprosdk.websockets.orders.events import OrderCreated

LOG = logging.getLogger(__name__)


class OrdersMessageHandler:
    """Handles orders channel messages"""

    def __init__(self, state: AccountState = None):
        self.state = state

    def handle_message(self, json_message: json):
        """Log result depending on the received message"""
        if json_message["type"] == "ORDER_CREATED":
            created = OrderCreated(**json_message["order"])
            LOG.debug("Created order %s", created)
            self.state.order_created(created)
        elif json_message["type"] == "ORDER_SUBMITTED_FOR_CANCELLATION":
            LOG.debug("Submitted for cancellation %s", json_message)
        elif json_message["type"] == "ORDER_CREATION_FAILED":
            LOG.error("Failed to create order due to %s", json_message)
        else:
            LOG.info("Unhandled event from ORDERS channel %s", json_message)
