import asyncio
import json
import logging
import uuid
from decimal import Decimal

from bpprosdk.websockets.orders.cancel_order import CancelOrderByClientId
from bpprosdk.websockets.orders.create_order import CreateOrder, LimitOrder, Side
from bpprosdk.websockets.websocket_client_advanced import AdvancedBitpandaProWebsocketClient


async def main():
    when_order_created = asyncio.get_event_loop().create_future()
    when_order_cancelled = asyncio.get_event_loop().create_future()

    async def handle_message(event: json):
        LOG.info("%s", event)
        if event["type"] == "ORDER_CREATED":
            when_order_created.set_result("created...")
        elif event["type"] == "ORDER_SUBMITTED_FOR_CANCELLATION":
            when_order_cancelled.set_result("cancelled...")

    # add your api token
    my_api_token = "eyJ..."

    bp_client = AdvancedBitpandaProWebsocketClient(
        api_token=my_api_token,
        wss_host="wss://streams.exchange.bitpanda.com",
        callback=handle_message
    )

    # Activates ACCOUNT_HISTORY, TRADING & ORDERS channel
    await bp_client.start_with(None, True)

    client_id = str(uuid.uuid4())
    new_order_with_client_id = CreateOrder(LimitOrder("BTC_EUR", Side.buy, Decimal('0.01'), Decimal('1000.50'), client_id))
    LOG.info("Creating new Order with client_id: %s", new_order_with_client_id)
    await bp_client.create_order(new_order_with_client_id)
    await when_order_created
    LOG.info("Balances: %s", bp_client.get_state().balances)
    LOG.info("Open orders: %s", bp_client.get_state().open_orders_by_order_id)

    LOG.info("Cancel Order with client_id: %s", client_id)
    await bp_client.cancel_order(CancelOrderByClientId(client_id))
    await when_order_cancelled
    LOG.info("Open orders: %s", bp_client.get_state().open_orders_by_order_id)

    await bp_client.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s\t%(levelname)-5s\t%(name)s\t%(message)s")
    LOG = logging.getLogger(__name__)

    asyncio.run(main())
