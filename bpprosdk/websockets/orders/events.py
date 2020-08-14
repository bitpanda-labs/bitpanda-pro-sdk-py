"""Events emitted by Orders Channel"""
import uuid

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class OrderCreated:
    """Response for successful order creation."""
    order_id: uuid
    account_id: uuid
    type: str
    time_in_force: str
    instrument_code: str
    side: str
    price: Decimal
    amount: Decimal
    filled_amount: Decimal
    is_post_only: str
    time: str
    client_id: uuid = None
    trigger_price: Decimal = None


@dataclass
class OrderSubmittedForCancellation:
    """Response for successful submission of an order cancellation."""
    order_id: uuid
    client_id: uuid
    remaining: Decimal
    order_book_sequence: int
