"""Websocket tests"""
# pylint: disable=no-member
import json
import logging
import os
import pytest
import uuid
from decimal import Decimal

from bpprosdk.websockets.orders.cancel_order import CancelOrderByClientId
from bpprosdk.websockets.orders.create_order import CreateOrder, Side, MarketOrder, LimitOrder, StopOrder, TimeInForce
from bpprosdk.websockets.subscriptions import Subscriptions, ChannelName, OrdersSubscription
from bpprosdk.websockets.unsubscription import Unsubscription
from bpprosdk.websockets.websocket_client import BitpandaProWebsocketClient
from bpprosdk.websockets.websocket_client_advanced import AdvancedBitpandaProWebsocketClient

LOG = logging.getLogger(__name__)


def test_verify_limit_order_payload():
    """Verify limit order structure"""
    raw = CreateOrder(LimitOrder("BTC_EUR", Side.buy, 1.2, 5000.50))
    as_json_string = raw.to_json()
    LOG.debug("limit_order: %s", as_json_string)
    limit_order = json.loads(as_json_string)
    assert limit_order["type"] == "CREATE_ORDER"
    result = limit_order["order"]
    assert result["time_in_force"] == "GOOD_TILL_CANCELLED"
    assert result["instrument_code"] == "BTC_EUR"
    assert result["type"] == "LIMIT"
    assert result["side"] == "BUY"
    assert Decimal(result["amount"]) == Decimal(1.2)
    assert Decimal(result["price"]) == Decimal(5000.50)


def test_verify_limit_order_supports_time_in_force():
    """Verify limit order with time_in_force structure"""
    raw = CreateOrder(LimitOrder("BTC_EUR", Side.sell, 0.12, 123.0, None, TimeInForce.fill_or_kill))
    as_json_string = raw.to_json()
    LOG.debug("limit_order: %s", as_json_string)
    limit_order = json.loads(as_json_string)
    assert limit_order["type"] == "CREATE_ORDER"
    result = limit_order["order"]
    assert result["time_in_force"] == "FILL_OR_KILL"
    assert result["instrument_code"] == "BTC_EUR"
    assert result["type"] == "LIMIT"
    assert result["side"] == "SELL"
    assert Decimal(result["amount"]) == Decimal(0.12)
    assert Decimal(result["price"]) == Decimal(123.0)


def test_verify_market_order_payload():
    """Verify market order structure"""
    raw = CreateOrder(MarketOrder("BTC_EUR", Side.sell, 0.05))
    as_json_string = raw.to_json()
    LOG.debug("market_order: %s", as_json_string)
    market_order = json.loads(as_json_string)
    assert market_order["type"] == "CREATE_ORDER"
    result = market_order["order"]
    assert result["instrument_code"] == "BTC_EUR"
    assert result["type"] == "MARKET"
    assert result["side"] == "SELL"
    assert Decimal(result["amount"]) == Decimal(0.05)


def test_verify_stop_order_payload():
    """Verify stop order structure"""
    raw = CreateOrder(StopOrder("BTC_EUR", Side.sell, 1.23, 5000.50, 5001))
    as_json_string = raw.to_json()
    LOG.debug("stop_order: %s", as_json_string)
    stop_order = json.loads(as_json_string)
    assert stop_order["type"] == "CREATE_ORDER"
    result = stop_order["order"]
    assert result["instrument_code"] == "BTC_EUR"
    assert result["type"] == "STOP"
    assert result["side"] == "SELL"
    assert Decimal(result["amount"]) == Decimal(1.23)
    assert Decimal(result["price"]) == Decimal(5000.50)
    assert Decimal(result["trigger_price"]) == Decimal(5001)


def test_verify_client_id():
    """Verify that client_id is accepted"""
    my_client_id = str(uuid.uuid4())
    as_json_string = CreateOrder(LimitOrder("BTC_EUR", Side.buy, 1.2, 5000.50, my_client_id)).to_json()
    LOG.debug("order: %s", as_json_string)
    limit_order = json.loads(as_json_string)
    assert str(my_client_id) == limit_order["order"]["client_id"]

    as_json_string = CreateOrder(StopOrder("BTC_EUR", Side.buy, 1.2, 5000.50, 5000, my_client_id)).to_json()
    LOG.debug("order: %s", as_json_string)
    stop_order = json.loads(as_json_string)
    assert str(my_client_id) == stop_order["order"]["client_id"]


@pytest.mark.asyncio
async def test_message_handling_of_orders_channel_by_using_order_id():
    """Tests handling of messages of the orders channel"""
    async def handle_message(json_message):
        LOG.debug("ignored message %s", json_message)

    client = AdvancedBitpandaProWebsocketClient(None, 'test', handle_message)
    order_creation = '{"order":{"time_in_force":"GOOD_TILL_CANCELLED","is_post_only":false,' \
                     '"order_id":"c241b172-ee8d-4e1b-8900-6512c2c23579",' \
                     '"account_id":"379a12c0-4560-11e9-82fe-2b25c6f7d123","instrument_code":"BTC_EUR",' \
                     '"time":"2020-06-02T06:48:08.278Z","side":"BUY","price":"6000.0","amount":"1.0",' \
                     '"filled_amount":"0.0","type":"LIMIT"},"channel_name":"ORDERS","type":"ORDER_CREATED",' \
                     '"time":"2020-06-02T06:48:08.278Z"} '
    await client.handle_message(json.loads(order_creation))
    assert len(client.state.open_orders_by_client_id) == 0
    assert len(client.state.open_orders_by_order_id) == 1
    order_cancellation = '{"order_id":"c241b172-ee8d-4e1b-8900-6512c2c23579","channel_name":"ORDERS",' \
                         '"type":"ORDER_SUBMITTED_FOR_CANCELLATION","time":"2020-06-02T06:48:08.381Z"} '
    await client.handle_message(json.loads(order_cancellation))
    assert len(client.state.open_orders_by_client_id) == 0
    # Open order is removed from store on trading channel update
    assert len(client.state.open_orders_by_order_id) == 1


@pytest.mark.asyncio
async def test_message_handling_of_orders_channel_by_using_client_id():
    """Tests handling of messages of the orders channel"""
    async def handle_message(json_message):
        LOG.debug("ignored message %s", json_message)

    client = AdvancedBitpandaProWebsocketClient(None, 'test', handle_message)
    order_creation = '{"order":{"time_in_force":"GOOD_TILL_CANCELLED","is_post_only":false,' \
                     '"order_id":"c241b172-ee8d-4e1b-8900-6512c2c23579",' \
                     '"client_id":"cd62ef52-048f-4395-b66f-1af28625f393",' \
                     '"account_id":"379a12c0-4560-11e9-82fe-2b25c6f7d123","instrument_code":"BTC_EUR",' \
                     '"time":"2020-06-02T06:48:08.278Z","side":"BUY","price":"6000.0","amount":"1.0",' \
                     '"filled_amount":"0.0","type":"LIMIT"},"channel_name":"ORDERS","type":"ORDER_CREATED",' \
                     '"time":"2020-06-02T06:48:08.278Z"} '
    await client.handle_message(json.loads(order_creation))
    assert len(client.state.open_orders_by_client_id) == 1
    assert len(client.state.open_orders_by_order_id) == 1
    order_cancellation = '{"client_id":"cd62ef52-048f-4395-b66f-1af28625f393","channel_name":"ORDERS",' \
                         '"type":"ORDER_SUBMITTED_FOR_CANCELLATION","time":"2020-06-02T06:48:08.381Z"} '
    await client.handle_message(json.loads(order_cancellation))
    # Open order is removed from store on trading channel update
    assert len(client.state.open_orders_by_client_id) == 1
    assert len(client.state.open_orders_by_order_id) == 1


@pytest.mark.asyncio
async def test_verify_successful_orders_channel_subscription(event_loop):
    """Tests subscribe / unsubscribe of the orders channel"""
    api_token = os.environ['BP_PRO_API_TOKEN']
    test_host = os.environ['TEST_HOST']
    when_subscribed = event_loop.create_future()
    when_order_created = event_loop.create_future()
    when_order_cancelled = event_loop.create_future()
    when_unsubscribed = event_loop.create_future()

    async def handle_message(json_message):
        if json_message["type"] == "SUBSCRIPTIONS":
            when_subscribed.set_result("subscribed")
        elif json_message["type"] == "UNSUBSCRIBED":
            when_unsubscribed.set_result("unsubscribed")
        elif json_message["type"] == "ORDER_CREATED":
            when_order_created.set_result("Order created")
        elif json_message["type"] == "ORDER_SUBMITTED_FOR_CANCELLATION":
            when_order_cancelled.set_result("Order cancelled")
        else:
            LOG.info("Ignored Message %s", json_message)

    client = BitpandaProWebsocketClient(api_token, test_host, handle_message)
    subscription = OrdersSubscription()
    await client.start(Subscriptions([subscription]))
    LOG.info(await when_subscribed)
    my_client_id = uuid.uuid4()
    await client.create_order(CreateOrder(LimitOrder("BTC_EUR", Side.buy, 0.01, 5000.50, str(my_client_id))))
    LOG.info(await when_order_created)
    await client.cancel_order(CancelOrderByClientId(my_client_id))
    LOG.info(await when_order_cancelled)
    await client.unsubscribe(Unsubscription([ChannelName.orders.value]))
    LOG.info(await when_unsubscribed)
    await client.close()
