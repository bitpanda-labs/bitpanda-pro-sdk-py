"""Test storing of bids and asks in Order book"""
import json
import logging

from bpprosdk.websockets.orderbook.orderbook import OrderBook

LOG = logging.getLogger(__name__)


def test_init_order_book_with_snapshot():
    """Construct order book by passing a snapshot message"""
    raw_snapshot = '{"instrument_code":"BTC_EUR","bids":[["8860.92","0.43712"],["8858.75","0.03225"],["8856.0",' \
                   '"0.15857"],["8855.0","0.45334"],["8852.11","0.0216"],["8850.0","0.60744"],["8845.01","3.45043"],' \
                   '["8845.0","3.52483"],["8838.77","0.51727"],["8835.0","0.00991"]],"asks":[["8874.23","0.36287"],' \
                   '["8876.4","0.0123"],["8883.0","0.43531"],["8884.0","1.11066"],["8885.99","2.27369"],["8886.0",' \
                   '"0.08116"],["8887.0","0.30046"],["8888.0","0.44740"],["8890.0","0.993"],["8896.42","0.42775"]],' \
                   '"channel_name":"ORDER_BOOK","type":"ORDER_BOOK_SNAPSHOT","time":"2020-07-15T12:05:02.365Z"}'
    store = OrderBook()
    store.init_with_snapshot(json.loads(raw_snapshot))
    assert len(store.get_asks()) == 10, "expected 10 asks"
    assert len(store.get_bids()) == 10, "expected 10 bids"


def test_update_order_book():
    """Construct order book by passing a snapshot message"""
    raw_snapshot = '{"instrument_code":"BTC_EUR","bids":[["8500.50","0.5"],["8858.75","0.03225"]],"asks":[["8600.10",' \
                   '"0.36287"],["8601.4","0.0123"]],"channel_name":"ORDER_BOOK","type":"ORDER_BOOK_SNAPSHOT",' \
                   '"time":"2020-07-15T12:05:02.365Z"}'
    store = OrderBook()
    store.init_with_snapshot(json.loads(raw_snapshot))
    assert len(store.get_asks()) == 2, "expected 2 asks"
    assert len(store.get_bids()) == 2, "expected 2 bids"

    add_1_ask_3_bids = '{"instrument_code":"BTC_EUR","changes":[["BUY","8845.0","0.1"],["SELL","8890","1.1928"],' \
                       '["BUY","8857.0","1.73595"],["BUY","8853.0","1.3326"]],' \
                       '"channel_name":"ORDER_BOOK","type":"ORDER_BOOK_UPDATE","time":"2020-07-15T12:05:03.777Z"}'
    store.update(json.loads(add_1_ask_3_bids))
    assert len(store.get_asks()) == 3, "expected 3 asks"
    assert len(store.get_bids()) == 5, "expected 5 bids"

    replace_ask_replace_bid = '{"instrument_code":"BTC_EUR","changes":[["SELL","8925.83","0.4"],["SELL","8890","0"],' \
                              '["BUY","8845.0","0"],["BUY","8858.75","0"]],"channel_name":"ORDER_BOOK",' \
                              '"type":"ORDER_BOOK_UPDATE","time":"2020-07-15T12:05:03.917Z"}'
    store.update(json.loads(replace_ask_replace_bid))
    assert len(store.get_asks()) == 3, "expected 3 asks"
    assert len(store.get_bids()) == 3, "expected 3 bids"
