# pylint: skip-file
"""Events to create orders via order channel"""
from abc import ABC
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from decimal import Decimal
from enum import Enum
from typing import Optional


class OrderType(Enum):
    limit = "LIMIT"
    stop = "STOP"
    market = "MARKET"


class Side(Enum):
    buy = "BUY"
    sell = "SELL"


class TimeInForce(Enum):
    good_till_cancelled = "GOOD_TILL_CANCELLED"
    good_till_time = "GOOD_TILL_TIME"
    immediate_or_cancel = "IMMEDIATE_OR_CANCELLED"
    fill_or_kill = "FILL_OR_KILL"


class Order(ABC):
    pass


@dataclass_json
@dataclass
class LimitOrder(Order):
    """Order payload with properties."""
    instrument_code: str
    side: Side
    amount: Decimal
    price: Decimal
    client_id: Optional[str] = None
    time_in_force: str = TimeInForce.good_till_cancelled
    type: OrderType = OrderType.limit


@dataclass_json
@dataclass
class MarketOrder(Order):
    """Market Order payload with properties."""
    instrument_code: str
    side: Side
    amount: Decimal
    type: OrderType = OrderType.market


@dataclass_json
@dataclass
class StopOrder(Order):
    """Stop Order payload with properties."""
    instrument_code: str
    side: Side
    amount: Decimal
    price: Decimal
    trigger_price: Decimal
    client_id: Optional[str] = None
    type: OrderType = OrderType.stop


@dataclass_json
@dataclass
class CreateOrder:
    """Create order payload."""
    order: Order
    type: str = 'CREATE_ORDER'
