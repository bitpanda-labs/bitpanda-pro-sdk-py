import asyncio
import json
import logging

from bpprosdk.websockets.subscriptions import OrderBookSubscription, Subscriptions
from bpprosdk.websockets.websocket_client import BitpandaProWebsocketClient


async def main():
    when_msg_received = asyncio.get_event_loop().create_future()

    async def handle_message(event: json):
        LOG.info("%s", event)
        # ... add custom code here
        if when_msg_received.done() is False:
            when_msg_received.set_result("Received a message...")

    bp_client = BitpandaProWebsocketClient(
        api_token=None,
        wss_host="wss://streams.exchange.bitpanda.com",
        callback=handle_message
    )

    order_book_subscription = OrderBookSubscription(["BTC_EUR", "BEST_EUR"])
    await bp_client.start(Subscriptions([order_book_subscription]))
    # ...
    await when_msg_received
    # ...
    await bp_client.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s\t%(levelname)-5s\t%(name)s\t%(message)s")
    LOG = logging.getLogger(__name__)

    asyncio.run(main())
