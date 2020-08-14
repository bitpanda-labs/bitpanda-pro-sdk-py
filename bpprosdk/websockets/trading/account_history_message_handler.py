"""Handles all messages coming from account history channel"""
# pylint: disable=no-member
import json
import logging

from bpprosdk.websockets.account.account_state import AccountState
from bpprosdk.websockets.trading.account_history_channel_payloads import AccountBalances, ActiveOrdersSnapshot, \
    InactiveOrdersSnapshot, OrderCreatedUpdate, OrderClosedUpdate, TradeSettledUpdate, FundsDeposited, FundsWithdrawn

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler())


class AccountHistoryMessageHandler:
    """Handles trading channel messages"""

    def __init__(self, state: AccountState = None):
        self.state = state

    def handle_message(self, json_message: json):
        """Updates the state depending on the received message"""
        if json_message["type"] == "BALANCES_SNAPSHOT":
            LOG.debug("Handling BALANCES_SNAPSHOT")
            balances = AccountBalances.from_json(json.dumps(json_message))
            self.state.init_balances(balances)
        elif json_message["type"] == "ACTIVE_ORDERS_SNAPSHOT":
            LOG.debug("Handling ACTIVE_ORDERS_SNAPSHOT")
            active_orders_snapshot = ActiveOrdersSnapshot.from_json(json.dumps(json_message))
            self.state.init_open_orders(active_orders_snapshot)
        elif json_message["type"] == "INACTIVE_ORDERS_SNAPSHOT":
            LOG.debug("Handling INACTIVE_ORDERS_SNAPSHOT")
            inactive_orders_snapshot = InactiveOrdersSnapshot.from_json(json.dumps(json_message))
            self.state.init_inactive_orders_for_last_24hours(inactive_orders_snapshot)
        elif json_message["type"] == "ACCOUNT_UPDATE":
            LOG.debug("Handling ACCOUNT_UPDATE")
            update_message = json_message["update"]
            if update_message["type"] == "ORDER_CREATED":
                updated_order = OrderCreatedUpdate.from_json(json.dumps(update_message))
                self.state.update_balance_on_order_created(updated_order.sequence, updated_order.locked)
            elif update_message["type"] == "ORDER_CLOSED":
                closed_order = OrderClosedUpdate.from_json(json.dumps(update_message))
                self.state.update_balance_on_closed_order(closed_order)
            elif update_message["type"] == "TRADE_SETTLED":
                trade_update = TradeSettledUpdate.from_json(json.dumps(update_message))
                self.state.update_balances_on_trade_settled(trade_update)
            elif update_message["type"] == "FUNDS_DEPOSITED":
                deposit = FundsDeposited.from_json(json.dumps(update_message))
                self.state.update_balances_on_deposit(deposit)
            elif update_message["type"] == "FUNDS_WITHDRAWN":
                withdrawal = FundsWithdrawn.from_json(json.dumps(update_message))
                self.state.update_balances_on_withdrawal(withdrawal)
            else:
                LOG.warning("Unhandled ACCOUNT_UPDATE event %s", update_message)
        elif json_message["type"] == "ORDER_REJECTED":
            LOG.error("An order was rejected: %s", json_message)
        else:
            LOG.info("Unhandled event from ACCOUNT_HISTORY channel %s", json_message)
