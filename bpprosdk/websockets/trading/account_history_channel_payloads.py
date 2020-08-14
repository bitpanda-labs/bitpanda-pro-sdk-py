# pylint: skip-file
"""Events emitted by Account History Channel"""
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from decimal import Decimal
from typing import List, Optional


@dataclass_json
@dataclass
class Balance:
    currency_code: str
    change: Decimal
    available: Decimal
    locked: Decimal
    sequence: int
    time: str


@dataclass_json
@dataclass
class AccountBalances:
    account_id: str
    balances: List[Balance]
    channel_name: str
    type: str
    time: str


@dataclass_json
@dataclass
class Trade:
    trade_id: str
    order_id: str
    account_id: str
    amount: Decimal
    price: Decimal
    instrument_code: str
    side: str
    time: str
    sequence: Optional[int] = None


@dataclass_json
@dataclass
class Order:
    order_id: str
    type: str
    instrument_code: str
    side: str
    price: Decimal
    amount: Decimal
    filled_amount: Decimal
    is_post_only: bool
    time: str
    time_in_force: Optional[str] = None
    average_price: Optional[Decimal] = None
    status: Optional[str] = None
    sequence: Optional[int] = None
    client_id: Optional[str] = None


@dataclass_json
@dataclass
class Fee:
    fee_type: str
    fee_group_id: str
    fee_amount: Decimal
    fee_percentage: Decimal
    fee_currency: str
    collection_type: str
    running_trading_volume: Decimal


@dataclass_json
@dataclass
class FeeByOrder:
    order_id: str
    fee_amount: Decimal
    fee_currency: str


@dataclass_json
@dataclass
class TradeWithFees:
    trade: Trade
    fee: Fee


@dataclass_json
@dataclass
class OrderWithTrades:
    order: Order
    trades: List[TradeWithFees]


@dataclass_json
@dataclass
class ActiveOrdersSnapshot:
    account_id: str
    orders: List[OrderWithTrades]
    channel_name: str
    type: str
    time: str


@dataclass_json
@dataclass
class InactiveOrdersSnapshot:
    account_id: str
    orders: List[OrderWithTrades]
    channel_name: str
    type: str
    time: str


@dataclass_json
@dataclass
class BalanceUpdate:
    currency_code: str
    amount: Decimal
    new_available: Decimal
    new_locked: Decimal


@dataclass_json
@dataclass
class OrderCreatedUpdate:
    order_id: str
    sequence: int
    time: str
    order: Order
    locked: BalanceUpdate


@dataclass_json
@dataclass
class OrderClosedUpdate:
    type: str
    activity: str
    order_id: str
    sequence: int
    time: str
    unlocked: BalanceUpdate


@dataclass_json
@dataclass
class TradeSettledUpdate:
    order_id: str
    sequence: int
    time: str
    trade: Trade
    fee: Fee
    spent: BalanceUpdate
    credited: BalanceUpdate
    unlocked: BalanceUpdate


@dataclass_json
@dataclass
class FundsDeposited:
    id: str
    sequence: int
    time: str
    credited: BalanceUpdate


@dataclass_json
@dataclass
class FundsWithdrawn:
    id: str
    sequence: int
    time: str
    deducted: BalanceUpdate
