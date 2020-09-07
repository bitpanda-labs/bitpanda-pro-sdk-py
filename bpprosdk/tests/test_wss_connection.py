"""Websocket tests"""
import asyncio
import logging
import pytest

from bpprosdk.websockets.websocket_client import BitpandaProWebsocketClient

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio
LOG = logging.getLogger(__name__)


async def test_setup(event_loop):
    """Test to verify setup!"""
    await asyncio.sleep(0, loop=event_loop)


async def test_emit_heartbeat_on_idle_connection(event_loop):
    """Expecting heartbeat message from event emitter:
    {"subscription":"SYSTEM","channel_name":"SYSTEM","type":"HEARTBEAT","time":"YYYY-MM-ddTHH:mm:ss.0Z"}
    """
    future_result = event_loop.create_future()

    async def handle_message(json_message):
        LOG.info("emitted event %s", json_message)
        assert json_message["subscription"] == "SYSTEM"
        assert json_message["channel_name"] == "SYSTEM"
        assert json_message["type"] == "HEARTBEAT"
        future_result.set_result("Success")

    client = BitpandaProWebsocketClient(None, "wss://streams.exchange.bitpanda.com", handle_message)
    await client.start(None)
    LOG.info(await future_result)
    await client.close()
