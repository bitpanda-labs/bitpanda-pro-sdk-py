"""Websocket tests"""
import json
import logging
import os
import pytest

from bpprosdk.websockets.subscriptions import Subscriptions, ChannelName, TradingSubscription
from bpprosdk.websockets.unsubscription import Unsubscription
from bpprosdk.websockets.websocket_client_advanced import AdvancedBitpandaProWebsocketClient

pytestmark = pytest.mark.asyncio
LOG = logging.getLogger(__name__)


async def test_message_handling_of_trading_channel_events():
    """Tests handling of messages of the trading channel"""
    async def handle_message(json_message):
        LOG.debug("ignored message %s", json_message)

    client = AdvancedBitpandaProWebsocketClient(None, 'test', handle_message)
    client.apply_trading_buffer()
    order_creation = '{"order":{"time_in_force":"GOOD_TILL_CANCELLED","is_post_only":false,' \
                     '"order_id":"c241b172-ee8d-4e1b-8900-6512c2c23579",' \
                     '"account_id":"379a12c0-4560-11e9-82fe-2b25c6f7d123","instrument_code":"BTC_EUR",' \
                     '"time":"2020-06-02T06:48:08.278Z","side":"BUY","price":"6000.0","amount":"1.0",' \
                     '"filled_amount":"0.0","type":"LIMIT"},"channel_name":"ORDERS","type":"ORDER_CREATED",' \
                     '"time":"2020-06-02T06:48:08.278Z"}'
    await client.handle_message(json.loads(order_creation))
    assert len(client.state.open_orders_by_order_id) == 1
    order_booked = '{"order_book_sequence": 1, "instrument_code": "BTC_EUR", "order_id": ' \
                   '"c241b172-ee8d-4e1b-8900-6512c2c23579", "remaining": "1.0", "channel_name": "TRADING", ' \
                   '"type": "BOOKED", "time": "2020-06-02T06:48:08.279Z"}'
    await client.handle_message(json.loads(order_booked))
    assert len(client.state.open_orders_by_order_id) == 1
    order_filled = '{"order_book_sequence": 1, "side": "BUY", "amount": "1.0", "trade_id": ' \
                   '"c2591a26-5f76-401f-83ec-4d20657f2db3", "matched_as": "MAKER", "matched_amount": "0.1", ' \
                   '"matched_price": "6000.0", "instrument_code": "BTC_EUR", "order_id": ' \
                   '"c241b172-ee8d-4e1b-8900-6512c2c23579", "remaining": "0.9", "channel_name": "TRADING", ' \
                   '"type": "FILL", "time": "2020-06-02T06:49:08.279Z"}'
    await client.handle_message(json.loads(order_filled))
    assert len(client.state.open_orders_by_order_id) == 1

    order_filled_fully = '{"status": "FILLED_FULLY", "order_book_sequence": 1, "instrument_code": "BTC_EUR", ' \
                         '"order_id": "c241b172-ee8d-4e1b-8900-6512c2c23579", "remaining": "0.0", "channel_name": ' \
                         '"TRADING", "type": "DONE", "time": "2020-06-02T06:50:08.279Z"}'
    await client.handle_message(json.loads(order_filled_fully))
    assert len(client.state.open_orders_by_order_id) == 0


async def test_message_handling_of_stop_order_events():
    """Tests handling of messages of the trading channel"""
    async def handle_message(json_message):
        LOG.debug("ignored message %s", json_message)

    client = AdvancedBitpandaProWebsocketClient(None, 'test', handle_message)
    client.apply_trading_buffer()
    order_creation = '{"order":{"time_in_force":"GOOD_TILL_CANCELLED","is_post_only":false,"trigger_price":"359.71",' \
                     '"order_id":"c02b49a0-312b-42e4-803b-5ff2179c3d5f",' \
                     '"account_id":"379a12c0-4560-11e9-82fe-2b25c6f7d123","instrument_code":"ETH_EUR",' \
                     '"time":"2020-08-07T14:21:53.691Z","side":"BUY","price":"359.71","amount":"1.0",' \
                     '"filled_amount":"0.0","type":"STOP"},"channel_name":"ORDERS","type":"ORDER_CREATED",' \
                     '"time":"2020-08-07T14:21:53.691Z"}'
    await client.handle_message(json.loads(order_creation))
    assert len(client.state.open_orders_by_order_id) == 1

    stop_order_tracked = '{"order_book_sequence": 0, "trigger_price": "359.71", "current_price": "359.78", ' \
                         '"instrument_code": "ETH_EUR", "order_id": "c02b49a0-312b-42e4-803b-5ff2179c3d5f", ' \
                         '"remaining": "1.0", "channel_name": "TRADING", "type": "TRACKED", ' \
                         '"time": "2020-08-07T14:21:53.692Z"} '
    await client.handle_message(json.loads(stop_order_tracked))
    assert len(client.state.open_orders_by_order_id) == 1

    stop_order_triggered = '{"order_book_sequence": 1, "price": "359.71", "instrument_code": "ETH_EUR", "order_id": ' \
                           '"c02b49a0-312b-42e4-803b-5ff2179c3d5f", "remaining": "1.0", "channel_name": "TRADING", ' \
                           '"type": "TRIGGERED", "time": "2020-08-14T14:22:03.064Z"} '
    await client.handle_message(json.loads(stop_order_triggered))
    assert len(client.state.open_orders_by_order_id) == 1


async def test_handling_of_done_error_events():
    """Tests handling of error messages where type is DONE"""
    async def handle_message(json_message):
        LOG.debug("ignored message %s", json_message)

    client = AdvancedBitpandaProWebsocketClient(None, 'test', handle_message)
    client.apply_trading_buffer()
    # Matching order would have caused a self trade => so it is never booked
    self_trade_prevented = '{"status": "SELF_TRADE", "instrument_code": "ETH_EUR", "order_id": ' \
                           '"338b7543-95d3-4cb8-a264-ed4212da7d92", "client_id": ' \
                           '"58672b66-fc1b-4855-add7-5365297a7213", "remaining": "60.6767", "channel_name": ' \
                           '"TRADING", "type": "DONE", "time": "2020-09-15T12:57:39.737Z"} '
    await client.handle_message(json.loads(self_trade_prevented))
    assert len(client.state.open_orders_by_order_id) == 0

    # Only for market orders => when not enough funds have been locked the order fails
    insufficient_funds = '{"status": "INSUFFICIENT_FUNDS","instrument_code": "ETH_EUR","order_id": ' \
                         '"fb2d540e-6fe4-411c-8d91-7c94b94d1ae2","remaining": "1.0","channel_name": "TRADING",' \
                         '"type": "DONE","time": "2020-09-15T13:15:07.214Z"}'
    await client.handle_message(json.loads(insufficient_funds))
    assert len(client.state.open_orders_by_order_id) == 0

    # Only for market orders => when not enough liquidity is in the order book the market order fails
    insufficient_liquidity = '{"status": "INSUFFICIENT_LIQUIDITY","instrument_code": "ETH_EUR","order_id": ' \
                             '"80cf3fed-5766-4b5c-a378-213c5541bf5d","remaining": "80.0","channel_name": "TRADING",' \
                             '"type": "DONE","time": "2020-09-15T12:58:12.305Z"}'
    await client.handle_message(json.loads(insufficient_liquidity))
    assert len(client.state.open_orders_by_order_id) == 0

    # Internal system error => order was never booked
    time_to_market_exceeded = '{"status": "TIME_TO_MARKET_EXCEEDED","instrument_code": "ETH_EUR","order_id": ' \
                              '"bbf4780c-c26b-45dd-a17d-4d554a5b6e30","remaining": "34.0","channel_name": "TRADING",' \
                              '"type": "DONE","time": "2020-09-15T12:58:12.305Z"}'
    await client.handle_message(json.loads(time_to_market_exceeded))
    assert len(client.state.open_orders_by_order_id) == 0


@pytest.mark.asyncio
async def test_verify_successful_trading_subscription(event_loop):
    """Handle authenticate messages"""
    api_token = os.environ['BP_PRO_API_TOKEN']
    test_host = os.environ['TEST_HOST']
    future_subscribe = event_loop.create_future()
    future_unsubscribe = event_loop.create_future()

    async def handle_message(json_message):
        LOG.debug("emitted event %s", json_message)
        if json_message["type"] == "SUBSCRIPTIONS":
            LOG.debug("Subscribed to: %s", json_message["channels"][0]["name"])
            if "TRADING" in json_message["channels"][0]["name"]:
                LOG.debug("Subscribed to trading channel")
                future_subscribe.set_result("Success")
        elif json_message["type"] == "UNSUBSCRIBED" and json_message["channel_name"] == "TRADING":
            future_unsubscribe.set_result("Success")
        else:
            LOG.debug("Ignored Message")

    client = AdvancedBitpandaProWebsocketClient(api_token, test_host, handle_message)
    subscription = TradingSubscription()
    await client.start(Subscriptions([subscription]))
    LOG.info(await future_subscribe)
    await client.unsubscribe(Unsubscription([ChannelName.trading.value]))
    LOG.info(await future_unsubscribe)
    await client.close()
