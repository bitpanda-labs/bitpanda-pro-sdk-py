"""Order book Channel tests"""
import json
import logging
import os
import pytest

from bpprosdk.websockets.subscriptions import ChannelName, OrderBookSubscription, Subscriptions
from bpprosdk.websockets.unsubscription import Unsubscription
from bpprosdk.websockets.websocket_client import BitpandaProWebsocketClient
from bpprosdk.websockets.websocket_client_advanced import AdvancedBitpandaProWebsocketClient

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio
LOG = logging.getLogger(__name__)


async def test_verify_successful_order_book_subscription(event_loop):
    """test order book channel subscribe and unsubscribe"""
    test_host = os.environ['TEST_HOST']
    future_subscribe = event_loop.create_future()
    future_unsubscribe = event_loop.create_future()

    async def handle_message(json_message):
        LOG.debug("emitted event %s", json_message)
        if json_message["type"] == "SUBSCRIPTIONS":
            LOG.debug("Subscribed to order book channel")
            future_subscribe.set_result("Success")
        elif json_message["type"] == "UNSUBSCRIBED":
            LOG.debug("Unsubscribed from order book channel")
            future_unsubscribe.set_result("Success")
        else:
            LOG.debug("Ignored Message")

    client = BitpandaProWebsocketClient(None, test_host, handle_message)
    order_book_subscription = OrderBookSubscription(['BTC_EUR', 'BEST_EUR'])
    await client.start(Subscriptions([order_book_subscription]))
    LOG.debug(await future_subscribe)
    await client.unsubscribe(Unsubscription([ChannelName.order_book.value]))
    LOG.debug(await future_unsubscribe)
    await client.close()


async def test_verify_handling_of_order_books():
    """test that the client handles order book messages correctly"""

    async def log_messages(json_message):
        """Callback only logging messages"""
        LOG.debug("message: %s", json_message)

    client = AdvancedBitpandaProWebsocketClient(None, 'test', log_messages)
    subscription = '{"channels":[{"instrument_codes":["BTC_EUR","ETH_EUR"],"depth":200,"name":"ORDER_BOOK"}],' \
                   '"type":"SUBSCRIPTIONS","time":"2020-07-15T12:00:00.364Z"}'
    await client.handle_message(json.loads(subscription))
    empty_oder_book_btc_eur = client.get_order_book('BTC_EUR')
    assert bool(empty_oder_book_btc_eur.get_asks()) is False, "expected empty order book for btc_eur"
    assert bool(empty_oder_book_btc_eur.get_bids()) is False, "expected empty order book for btc_eur"
    empty_oder_book_eth_eur = client.get_order_book('ETH_EUR')
    assert bool(empty_oder_book_eth_eur.get_asks()) is False, "expected empty order book for eth_eur"
    assert bool(empty_oder_book_eth_eur.get_bids()) is False, "expected empty order book for eth_eur"
    raw_snapshot_btc_eur = '{"instrument_code":"BTC_EUR","bids":[["8860.92","0.43712"],["8858.75","0.03225"],' \
                           '["8856.0","0.15857"],["8855.0","0.45334"],["8852.11","0.0216"],["8850.0","0.60744"],' \
                           '["8845.01","3.45043"],["8845.0","3.52483"],["8838.77","0.51727"],["8835.0","0.00991"]],' \
                           '"asks":[["8874.23","0.36287"],["8876.4","0.0123"],["8883.0","0.43531"],["8884.0",' \
                           '"1.11066"],["8885.99","2.27369"],["8886.0","0.08116"],["8887.0","0.30046"],["8888.0",' \
                           '"0.44740"],["8890.0","0.993"],["8896.42","0.42775"]],"channel_name":"ORDER_BOOK",' \
                           '"type":"ORDER_BOOK_SNAPSHOT","time":"2020-07-15T12:00:00.365Z"}'
    await client.handle_message(json.loads(raw_snapshot_btc_eur))
    oder_book_btc_eur = client.get_order_book('BTC_EUR')
    assert bool(oder_book_btc_eur.get_asks()) is True, "expected asks for btc_eur"
    assert bool(oder_book_btc_eur.get_bids()) is True, "expected bids for btc_eur"
    raw_snapshot_eth_eur = '{"instrument_code":"ETH_EUR","bids":[["186.3","20.4"]],' \
                           '"asks":[["186.58","0.36287"]],"channel_name":"ORDER_BOOK",' \
                           '"type":"ORDER_BOOK_SNAPSHOT","time":"2020-07-15T12:00:00.366Z"}'
    await client.handle_message(json.loads(raw_snapshot_eth_eur))
    oder_book_eth_eur = client.get_order_book('ETH_EUR')
    assert bool(oder_book_eth_eur.get_asks()) is True, "expected asks for eth_eur"
    assert bool(oder_book_eth_eur.get_bids()) is True, "expected bids for eth_eur"
    unsubscribed = '{"channel_name":"ORDER_BOOK","type":"UNSUBSCRIBED","time":"2020-07-15T12:30:00.288Z"}'
    await client.handle_message(json.loads(unsubscribed))
    assert bool(client.get_order_books()) is False
