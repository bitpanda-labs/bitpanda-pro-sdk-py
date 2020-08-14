"""Events emitted by Trading Channel"""
import uuid

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from decimal import Decimal
from typing import Optional


@dataclass_json
@dataclass
class Fill:
    """The order was matched and (partially) filled."""
    order_id: uuid
    trade_id: uuid
    amount: Decimal
    remaining: Decimal
    side: str
    matched_as: str
    matched_amount: Decimal
    matched_price: Decimal
    order_book_sequence: int
    client_id: Optional[str] = None


@dataclass_json
@dataclass
class Booked:
    """
    The order was not fully filled immediately and is now open in the order book. Only limit orders can be booked.
    """
    order_id: uuid
    instrument_code: str
    remaining: Decimal
    order_book_sequence: int
    client_id: Optional[str] = None


@dataclass_json
@dataclass
class Done:
    """
    The order is not in the order book anymore. If an order is filled fully, all FILL events are sent and a final
    DONE event with remaining == 0.
    """
    order_id: uuid
    remaining: Decimal
    """
    FILL, FILLED_FULLY, CANCELLED, SELF_TRADE
    """
    status: str
    order_book_sequence: int
    client_id: Optional[str] = None


@dataclass_json
@dataclass
class Tracked:
    """
    The stop order is now being tracked by the order book and will trigger when its price is reached.
    """
    order_id: uuid
    instrument_code: str
    remaining: Decimal
    trigger_price: Decimal
    order_book_sequence: int
    client_id: Optional[str] = None


@dataclass_json
@dataclass
class Triggered:
    """
    The stop order is triggered and was converted into a limit order.
    """
    order_id: uuid
    instrument_code: str
    remaining: Decimal
    price: Decimal
    order_book_sequence: int
    client_id: Optional[str] = None
