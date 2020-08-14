"""Events to cancel orders via order channel"""
import json
import uuid

from dataclasses import dataclass


@dataclass
class CancelOrderByOrderId:
    """Cancel order payload."""
    order_id: uuid

    def as_json(self):
        """Returns a valid json as web socket request"""
        return json.dumps({
            "type": "CANCEL_ORDER",
            "order_id": str(self.order_id)
        })


@dataclass
class CancelOrderByClientId:
    """Cancel order payload."""
    client_id: uuid

    def as_json(self):
        """Returns a valid json as web socket request"""
        return json.dumps({
            "type": "CANCEL_ORDER",
            "client_id": str(self.client_id)
        })
