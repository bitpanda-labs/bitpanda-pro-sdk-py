"""Websocket tests for account history subscribtion"""
import json
import logging
import os
import pytest
from decimal import Decimal

from bpprosdk.websockets.subscriptions import Subscriptions, ChannelName, AccountHistorySubscription
from bpprosdk.websockets.unsubscription import Unsubscription
from bpprosdk.websockets.websocket_client import BitpandaProWebsocketClient
from bpprosdk.websockets.websocket_client_advanced import AdvancedBitpandaProWebsocketClient

pytestmark = pytest.mark.asyncio
LOG = logging.getLogger(__name__)

# Load JSON samples
with open("bpprosdk/tests/samples/balances_snapshot.json") as file:
    account_balances_json = json.load(file)

with open("bpprosdk/tests/samples/balances_deposit.json") as file:
    account_balance_deposit = json.load(file)

with open("bpprosdk/tests/samples/balances_withdrawal.json") as file:
    account_balance_withdrawal = json.load(file)

with open("bpprosdk/tests/samples/active_orders_snapshot.json") as file:
    active_orders_snapshot_json = json.load(file)

with open("bpprosdk/tests/samples/active_orders_snapshot_multiple_instruments.json") as file:
    active_orders_snapshot_multiple_instruments_json = json.load(file)

with open("bpprosdk/tests/samples/inactive_orders_snapshot.json") as file:
    inactive_orders_snapshot_json = json.load(file)

with open("bpprosdk/tests/samples/order_created_update.json") as file:
    order_created_json = json.load(file)

with open("bpprosdk/tests/samples/order_created_orders_channel.json") as file:
    order_created_orders_channel_json = json.load(file)

with open("bpprosdk/tests/samples/order_closed.json") as file:
    order_closed_json = json.load(file)

with open("bpprosdk/tests/samples/trade_settled_partially.json") as file:
    trade_settled_partially_json = json.load(file)

with open("bpprosdk/tests/samples/trade_settled_fully.json") as file:
    trade_settled_json = json.load(file)

with open("bpprosdk/tests/samples/trade_settled_fully_order_done.json") as file:
    trade_settled_order_done_json = json.load(file)

with open("bpprosdk/tests/samples/market_order_filled.json") as file:
    market_order_filled_json = json.load(file)

with open("bpprosdk/tests/samples/order_created_update_old_sequence.json") as file:
    old_seq_order_created_json = json.load(file)

with open("bpprosdk/tests/samples/order_created_update_newer_sequence.json") as file:
    newer_seq_order_created_json = json.load(file)


async def test_verify_successful_account_history_subscription(event_loop):
    """Test account history subscription handling"""
    api_token = os.environ["BP_PRO_API_TOKEN"]
    test_host = os.environ["TEST_HOST"]

    when_subscribed = event_loop.create_future()
    when_unsubscribed = event_loop.create_future()

    async def handle_message(json_message):
        if json_message["type"] == "SUBSCRIPTIONS":
            when_subscribed.set_result("subscribed")
        elif json_message["type"] == "UNSUBSCRIBED":
            when_unsubscribed.set_result("unsubscribed")
        else:
            LOG.info("Ignored Message %s", json_message)

    client = BitpandaProWebsocketClient(api_token, test_host, handle_message)
    subscription = AccountHistorySubscription()
    await client.start(Subscriptions([subscription]))
    LOG.info(await when_subscribed)
    await client.unsubscribe(Unsubscription([ChannelName.account_history.value]))
    LOG.info(await when_unsubscribed)
    await client.close()


async def log_messages(json_message):
    """Callback only logging messages"""
    LOG.debug("message: %s", json_message)


async def test_handle_account_balances():
    """Test account balance snapshot handling"""
    client = AdvancedBitpandaProWebsocketClient("irrelevant", "irrelevant", log_messages)
    await client.handle_message(account_balances_json)
    balance = client.state.balances["EUR"]
    assert balance.available == Decimal("6606076.62363137")


async def test_handle_active_orders_snapshot():
    """Test active orders snapshot handling"""
    client = AdvancedBitpandaProWebsocketClient("irrelevant", "irrelevant", log_messages)
    await client.handle_message(active_orders_snapshot_json)
    open_orders = client.state.open_orders_by_order_id
    assert len(open_orders) == 1, "expected 1 order"
    order = open_orders.get("6894fe05-4071-49ca-813e-d88d3621e168")
    assert order.instrument_code == "BTC_EUR"
    assert order.order_id == "6894fe05-4071-49ca-813e-d88d3621e168"
    assert order.type == "LIMIT"
    assert order.time_in_force == "GOOD_TILL_CANCELLED"
    assert order.side == "SELL"
    assert order.price == Decimal("18500.0")
    assert order.remaining == Decimal("0.1")
    assert order.client_id == "082e0b7c-1888-4db2-b53e-208b64ae09b3"


async def test_handle_active_orders_snapshot_multiple_instruments():
    """Test active orders snapshot handling"""
    client = AdvancedBitpandaProWebsocketClient("irrelevant", "irrelevant", log_messages)
    await client.handle_message(active_orders_snapshot_multiple_instruments_json)
    open_orders = client.state.open_orders_by_order_id
    assert len(open_orders) == 3
    btc_eur_order = open_orders.get("ce246752-18c9-41a1-872e-759a0016b9c3")
    assert btc_eur_order.instrument_code == "BTC_EUR"
    eth_eur_order = open_orders.get("94cd6c5a-5ab8-4678-b932-7f81083d1f08")
    assert eth_eur_order.instrument_code == "ETH_EUR"


async def test_handle_inactive_orders_snapshot():
    """Test handling of inactive orders snapshot"""
    client = AdvancedBitpandaProWebsocketClient("irrelevant", "irrelevant", log_messages)
    await client.handle_message(inactive_orders_snapshot_json)
    inactive_orders = client.state.last_24h_inactive_orders
    assert len(inactive_orders) == 4, "expected 4 orders"
    order = inactive_orders.get("297bd6d8-ae68-4547-b414-0bfc87d13019")
    assert order.instrument_code == "BTC_EUR"
    assert order.filled_amount == Decimal("0.2")


async def test_handle_order_created_and_then_close():
    """ Test handling of created order events"""
    client = AdvancedBitpandaProWebsocketClient("irrelevant", "irrelevant", log_messages)
    await client.handle_message(account_balances_json)
    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8975.828764802")
    assert balance.locked == Decimal("0.4")

    await client.handle_message(order_created_json)
    expected_order = client.state.open_orders_by_order_id.get("65ecb524-4a7f-4b22-aa44-ec0b38d3db9c")
    # Orders are handled through orders/trading channel
    assert expected_order is None

    # check balance
    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8974.828764802")
    assert balance.locked == Decimal("1.4")

    await client.handle_message(order_closed_json)

    order = client.state.open_orders_by_order_id.get("65ecb524-4a7f-4b22-aa44-ec0b38d3db9c")
    assert order is None
    inactive_order = client.state.inactive_orders.get("65ecb524-4a7f-4b22-aa44-ec0b38d3db9c")
    # Inactive Orders are handled through orders/trading channel
    assert inactive_order is None

    # check balance
    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8975.828764802")
    assert balance.locked == Decimal("0.4")


async def test_handle_trade_settled_updates():
    """Test trade settlement events"""
    client = AdvancedBitpandaProWebsocketClient("irrelevant", "irrelevant", log_messages)
    await client.handle_message(account_balances_json)
    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8975.828764802")
    assert balance.locked == Decimal("0.4")

    # ------- Order created  ----------
    await client.handle_message(order_created_json)
    expected_order = client.state.open_orders_by_order_id.get("65ecb524-4a7f-4b22-aa44-ec0b38d3db9c")
    # Orders are handled through orders/trading channel
    assert expected_order is None

    # On order channel update the order is in the store
    await client.handle_message(order_created_orders_channel_json)
    expected_order = client.state.open_orders_by_order_id.get("65ecb524-4a7f-4b22-aa44-ec0b38d3db9c")
    assert expected_order is not None
    assert expected_order.remaining == Decimal("1.0")
    assert expected_order.order_id == "65ecb524-4a7f-4b22-aa44-ec0b38d3db9c"
    assert expected_order.price == "8500.0"

    # check balance
    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8974.828764802")
    assert balance.locked == Decimal("1.4")

    # ------- half of order settled  ----------
    await client.handle_message(trade_settled_partially_json)
    # check balance again, partially filled
    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8974.828764802")
    assert balance.locked == Decimal("0.9")
    # order is still part of open orders
    expected_order = client.state.open_orders_by_order_id.get("65ecb524-4a7f-4b22-aa44-ec0b38d3db9c")
    assert expected_order is not None
    assert expected_order.remaining == Decimal("1.0")
    assert expected_order.order_id == "65ecb524-4a7f-4b22-aa44-ec0b38d3db9c"
    assert expected_order.price == "8500.0"

    # ------- fully settled  order ----------
    await client.handle_message(trade_settled_json)
    # check balance again, not locked anymore
    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8974.828764802")
    assert balance.locked == Decimal("0.4")
    # order is completed, on update from trading channel the store is updated
    client.apply_trading_buffer()
    await client.handle_message(trade_settled_order_done_json)

    expected_order = client.state.open_orders_by_order_id.get("65ecb524-4a7f-4b22-aa44-ec0b38d3db9c")
    assert expected_order is None
    inactive_order = client.state.inactive_orders.get("65ecb524-4a7f-4b22-aa44-ec0b38d3db9c")
    assert inactive_order is not None
    assert inactive_order.order_id == "65ecb524-4a7f-4b22-aa44-ec0b38d3db9c"
    assert inactive_order.remaining == Decimal("0.0")
    assert inactive_order.order_id == "65ecb524-4a7f-4b22-aa44-ec0b38d3db9c"
    assert inactive_order.price == "8500.0"


async def test_handle_out_of_order_sequenced_message():
    """Test situations when an event arrives with an older sequence"""
    client = AdvancedBitpandaProWebsocketClient("irrelevant", "irrelevant", log_messages)
    await client.handle_message(account_balances_json)

    await client.handle_message(order_created_json)
    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8974.828764802")
    assert balance.locked == Decimal("1.4")
    # an event with older sequence should be ignored, therefore no change in the balance
    await client.handle_message(old_seq_order_created_json)
    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8974.828764802")
    assert balance.locked == Decimal("1.4")
    # a newer event with higher sequence should be accepted
    await client.handle_message(newer_seq_order_created_json)
    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8569.228764802")
    assert balance.locked == Decimal("2.2")


async def test_deposit_of_funds():
    """Verify correct balance after deposit"""
    client = AdvancedBitpandaProWebsocketClient("irrelevant", "irrelevant", log_messages)
    await client.handle_message(account_balances_json)

    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8975.828764802")
    assert balance.locked == Decimal("0.4")

    balance = client.state.balances["EUR"]
    assert balance.available == Decimal("6606076.62363137")
    assert balance.locked == Decimal("0.0")

    # Change in BTC balance after 1.1 BTC deposit
    await client.handle_message(account_balance_deposit)
    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8976.938764802")
    assert balance.locked == Decimal("0.5")

    # No change in EUR balance
    balance = client.state.balances["EUR"]
    assert balance.available == Decimal("6606076.62363137")
    assert balance.locked == Decimal("0.0")


async def test_withdrawal_of_funds():
    """Verify correct balance after withdrawal"""
    client = AdvancedBitpandaProWebsocketClient("irrelevant", "irrelevant", log_messages)
    await client.handle_message(account_balances_json)

    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8975.828764802")
    assert balance.locked == Decimal("0.4")

    balance = client.state.balances["EUR"]
    assert balance.available == Decimal("6606076.62363137")
    assert balance.locked == Decimal("0.0")

    # Change in BTC balance after 0.22 BTC withdrawal
    await client.handle_message(account_balance_withdrawal)
    balance = client.state.balances["BTC"]
    assert balance.available == Decimal("8975.608764802")
    assert balance.locked == Decimal("0.12")

    # No change in EUR balance
    balance = client.state.balances["EUR"]
    assert balance.available == Decimal("6606076.62363137")
    assert balance.locked == Decimal("0.0")
