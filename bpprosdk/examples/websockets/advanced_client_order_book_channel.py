import asyncio
import json
import logging

from bpprosdk.websockets.subscriptions import OrderBookSubscription, Subscriptions
from bpprosdk.websockets.websocket_client_advanced import AdvancedBitpandaProWebsocketClient


async def main():
    when_msg_received = asyncio.get_event_loop().create_future()

    def handle_message(event: json):
        LOG.info("%s", event)
        if event["type"] == "ORDER_BOOK_SNAPSHOT":
            when_msg_received.set_result("snapshot received...")

    bp_client = AdvancedBitpandaProWebsocketClient(
        api_token=None,
        wss_host="wss://streams.exchange.bitpanda.com",
        callback=handle_message
    )

    order_book_subscription = OrderBookSubscription(["BTC_EUR"])
    # Order book subscription without ACCOUNT_HISTORY, TRADING & ORDERS channel
    await bp_client.start_with(Subscriptions([order_book_subscription]), False)

    await when_msg_received
    LOG.info("asks book BTC_EUR: %s", bp_client.get_order_book("BTC_EUR").asks)
    LOG.info("bids BTC_EUR: %s", bp_client.get_order_book("BTC_EUR").bids)
    await bp_client.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s\t%(levelname)-5s\t%(name)s\t%(message)s")
    LOG = logging.getLogger(__name__)

    asyncio.run(main())
