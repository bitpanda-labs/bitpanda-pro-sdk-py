"""Current state of balances, open order, trades, ..."""
import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from bpprosdk.websockets.orders.events import OrderCreated
from bpprosdk.websockets.trading.account_history_channel_payloads import AccountBalances, ActiveOrdersSnapshot, \
    InactiveOrdersSnapshot, OrderClosedUpdate, TradeSettledUpdate, BalanceUpdate, FundsDeposited, FundsWithdrawn
from bpprosdk.websockets.trading.trading_channel_events import Booked, Fill, Done, Tracked

LOG = logging.getLogger(__name__)


@dataclass
class FeeInfo:
    """Fee info per order."""
    fee_amount: Decimal
    fee_currency: str
    fee_percentage: Decimal
    fee_group_id: str
    fee_type: str
    collection_type: str
    running_trading_volume: Decimal


@dataclass
class OpenOrder:
    """Order as it is stored as open order."""
    instrument_code: str
    order_id: uuid
    type: str
    time_in_force: str
    side: str
    price: Decimal
    remaining: Decimal
    order_book_sequence: int
    client_id: Optional[str] = None


@dataclass
class InactiveOrder:
    """Order as it is stored as inactive order."""
    instrument_code: str
    order_id: uuid
    type: str
    time_in_force: str
    side: str
    price: Decimal
    remaining: Decimal
    order_book_sequence: int
    client_id: Optional[str] = None


@dataclass
class AccountState:
    """Represents the current state of one account"""
    balances: dict()
    open_orders_by_order_id: dict()
    open_orders_by_client_id: dict()
    # Orders that are done during the runtime of the application
    inactive_orders: dict()
    # Inactive orders from snapshot showing the last 24 hours
    last_24h_inactive_orders: dict()
    highest_sequence_per_instrument: dict()
    highest_account_history_sequence: dict()

    def flush_inactive_orders(self):
        """Flush inactive orders to free up space"""
        self.inactive_orders = dict()

    def is_account_history_sequence_number_higher(self, account_history_sequence: int, currency_code: str):
        """Account History sequence must increase per currency_code, otherwise it should be ignored"""
        current_sequence = self.highest_account_history_sequence.get(currency_code)
        if current_sequence is not None and account_history_sequence < current_sequence:
            LOG.warning("Ignoring update with sequence %i which is lower than highest encountered sequence %i for %s",
                        account_history_sequence, current_sequence, currency_code)
            return False
        self.highest_account_history_sequence.update({currency_code: account_history_sequence})
        return True

    # State updated by orders channel
    def order_created(self, created: OrderCreated):
        """Adding created order to store"""
        open_order = self.open_orders_by_order_id.get(created.order_id)
        if open_order is None:
            open_order = OpenOrder(
                created.instrument_code,
                created.order_id,
                created.type,
                created.time_in_force,
                created.side,
                created.price,
                Decimal(created.amount),
                0,
                created.client_id
            )
            self.open_orders_by_order_id.update({open_order.order_id: open_order})
            if created.client_id is not None:
                self.open_orders_by_client_id.update({open_order.client_id: open_order})

    # State updated by trading channel
    def update_open_orders(self, booked_order: Booked):
        """When the order is booked we are updating the store"""
        highest_known = self.highest_sequence_per_instrument.get(booked_order.instrument_code)
        if highest_known is None or booked_order.order_book_sequence > highest_known:
            open_order = self.open_orders_by_order_id.get(booked_order.order_id)
            if open_order is not None:
                open_order.remaining = booked_order.remaining
                open_order.order_book_sequence = booked_order.order_book_sequence
                self.open_orders_by_order_id.update({open_order.order_id: open_order})
                LOG.debug("Updated order in store: %s", open_order)
                code = open_order.instrument_code
                self.highest_sequence_per_instrument.update({code: open_order.order_book_sequence})
                if open_order.client_id is not None:
                    self.open_orders_by_client_id.update({open_order.client_id: open_order})

    def update_open_orders_on_stop_order(self, tracked_order: Tracked):
        """Creation of stop orders yields a tracked message instead of booked"""
        highest_known = self.highest_sequence_per_instrument.get(tracked_order.instrument_code)
        if highest_known is None or tracked_order.order_book_sequence > highest_known:
            open_order = self.open_orders_by_order_id.get(tracked_order.order_id)
            if open_order is not None:
                open_order.remaining = tracked_order.remaining
                open_order.order_book_sequence = tracked_order.order_book_sequence
                self.open_orders_by_order_id.update({open_order.order_id: open_order})
                LOG.debug("Updated stop order in store: %s", open_order)
                code = open_order.instrument_code
                self.highest_sequence_per_instrument.update({code: open_order.order_book_sequence})
                if open_order.client_id is not None:
                    self.open_orders_by_client_id.update({open_order.client_id: open_order})

    def fill_open_order(self, fill: Fill):
        """Update open order with information from fill event"""
        LOG.info("Fill open order!")
        open_order = self.open_orders_by_order_id.get(fill.order_id)
        if open_order is not None:
            if open_order.remaining > fill.remaining:
                open_order.remaining = fill.remaining
                self.open_orders_by_order_id.update({open_order.order_id: open_order})

        if fill.client_id is not None:
            open_order_by_client_id = self.open_orders_by_client_id.get(fill.client_id)
            if open_order_by_client_id is not None:
                open_order_by_client_id.remaining = fill.remaining
                self.open_orders_by_client_id.update({open_order_by_client_id.order_id: open_order_by_client_id})

    def order_done(self, done: Done):
        """Either fully filled or cancelled removes the order from the store"""
        removed = self.open_orders_by_order_id.pop(done.order_id, None)
        if removed is None:
            LOG.error("No order found for order_id %s. State may be out of sync.", done.order_id)
        else:
            inactive_order = InactiveOrder(
                removed.instrument_code,
                removed.order_id,
                removed.type,
                removed.time_in_force,
                removed.side,
                removed.price,
                done.remaining,
                done.order_book_sequence,
                done.client_id
            )
            self.inactive_orders.update({inactive_order.order_id: inactive_order})

        if done.client_id is not None:
            removed_client_id = self.open_orders_by_client_id.pop(done.client_id, None)
            if removed_client_id is None:
                LOG.error("No order found for client_id %s. State may be out of sync.", done.client_id)

    # State updated by account history channel
    def init_balances(self, account_balances: AccountBalances):
        """Initialise balances by consuming the balance snapshot from account history"""
        for balance in account_balances.balances:
            current_balance = self.balances.get(balance.currency_code)
            if current_balance is not None:
                # When snapshot is delayed, only add when sequence is higher
                if current_balance.sequence < balance.sequence:
                    self.balances.update({balance.currency_code: balance})
            else:
                self.balances.update({balance.currency_code: balance})

    def init_open_orders(self, active_orders_snapshot: ActiveOrdersSnapshot):
        """Initialise open orders snapshot from account history"""
        for order_with_trades in active_orders_snapshot.orders:
            snapshot_order = order_with_trades.order
            open_order = OpenOrder(
                snapshot_order.instrument_code,
                snapshot_order.order_id,
                snapshot_order.type,
                snapshot_order.time_in_force,
                snapshot_order.side,
                snapshot_order.price,
                snapshot_order.amount - snapshot_order.filled_amount,
                0,
                snapshot_order.client_id
            )
            self.open_orders_by_order_id.update({open_order.order_id: open_order})
            if open_order.client_id is not None:
                self.open_orders_by_client_id.update({open_order.client_id: open_order})

    def init_inactive_orders_for_last_24hours(self, inactive_orders_snapshot: InactiveOrdersSnapshot):
        """Historical inactive orders for the last 24 hours"""
        self.last_24h_inactive_orders.update({order_with_trades.order.order_id: order_with_trades.order
                                              for order_with_trades in inactive_orders_snapshot.orders})

    def update_balance_on_order_created(self, event_sequence: int, locked: BalanceUpdate):
        """Updates balance on order creation"""
        if self.is_account_history_sequence_number_higher(event_sequence, locked.currency_code):
            self.balances.get(locked.currency_code).available = locked.new_available
            self.balances.get(locked.currency_code).locked = locked.new_locked

    def update_balances_on_trade_settled(self, trade_update: TradeSettledUpdate):
        """Updates balances as trading channel does not contain balance information"""
        if self.is_account_history_sequence_number_higher(trade_update.sequence, trade_update.spent.currency_code):
            # Update balance from spent currency
            self.balances.get(trade_update.spent.currency_code).available = trade_update.spent.new_available
            self.balances.get(trade_update.spent.currency_code).locked = trade_update.spent.new_locked

        if self.is_account_history_sequence_number_higher(trade_update.sequence, trade_update.credited.currency_code):
            # Update balance from credited currency
            self.balances.get(trade_update.credited.currency_code).available = trade_update.credited.new_available
            self.balances.get(trade_update.credited.currency_code).locked = trade_update.credited.new_locked

        if self.is_account_history_sequence_number_higher(trade_update.sequence, trade_update.unlocked.currency_code):
            # Update balance from unlocked currency
            self.balances.get(trade_update.unlocked.currency_code).available = trade_update.unlocked.new_available
            self.balances.get(trade_update.unlocked.currency_code).locked = trade_update.unlocked.new_locked

    def update_balance_on_closed_order(self, order_closed: OrderClosedUpdate):
        """Updates balance on order close"""
        if self.is_account_history_sequence_number_higher(order_closed.sequence, order_closed.unlocked.currency_code):
            self.balances.get(order_closed.unlocked.currency_code).available = order_closed.unlocked.new_available
            self.balances.get(order_closed.unlocked.currency_code).locked = order_closed.unlocked.new_locked

    def update_balances_on_deposit(self, deposit: FundsDeposited):
        """Updates balance on deposit"""
        if self.is_account_history_sequence_number_higher(deposit.sequence, deposit.credited.currency_code):
            self.balances.get(deposit.credited.currency_code).available = deposit.credited.new_available
            self.balances.get(deposit.credited.currency_code).locked = deposit.credited.new_locked

    def update_balances_on_withdrawal(self, withdrawal: FundsWithdrawn):
        """Updates balance on deposit"""
        if self.is_account_history_sequence_number_higher(withdrawal.sequence, withdrawal.deducted.currency_code):
            self.balances.get(withdrawal.deducted.currency_code).available = withdrawal.deducted.new_available
            self.balances.get(withdrawal.deducted.currency_code).locked = withdrawal.deducted.new_locked
