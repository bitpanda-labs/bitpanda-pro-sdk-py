"""Websocket client which emits all events"""
import asyncio
import json
import logging
import typing
import websockets

from bpprosdk.websockets.orders.cancel_order import CancelOrderByClientId, CancelOrderByOrderId
from bpprosdk.websockets.orders.create_order import CreateOrder
from bpprosdk.websockets.subscriptions import Subscriptions
from bpprosdk.websockets.unsubscription import Unsubscription

LOG = logging.getLogger(__name__)


class BitpandaProWebsocketClient:
    """Provides methods to interact with the web socket connection and emits the received messages."""

    def __init__(self, api_token=None, wss_host=None, callback=None):
        LOG.debug("init client...")
        self.api_token = api_token
        self.host = wss_host
        self.connection = None
        self.callback = callback
        if callback is None:
            LOG.error("No callback configured!")
            raise Exception("Callback required.")

    def handle_message(self, json_message: json):
        """Calls provided callback and passes json messages"""
        self.callback(json_message)

    # pylint: disable=broad-except
    async def start(self, subscriptions: Subscriptions):
        """Start websocket connection"""
        LOG.debug("creating new connection...")
        when_connected = asyncio.get_event_loop().create_future()
        try:
            # Get the current event loop.
            loop = asyncio.get_running_loop()
            loop.create_task(
                self.consume_messages(when_connected, subscriptions)
            )
            await when_connected
        except Exception:
            LOG.exception("Unexpected Exception occurred :( Closing...")
            await self.close()

    async def consume_messages(self, when_connected: asyncio.Future, subscriptions: Subscriptions):
        """Consumes messages form the open web socket connection and forwards them to the callback"""
        self.connection = await websockets.connect(self.host, ssl=True)
        if subscriptions is None:
            # When no subscriptions are added we complete on connect
            when_connected.set_result("Connected")

        if self.api_token is not None:
            auth_message = self.get_auth_message_as_json()
            await self.send_message(auth_message)
        else:
            # Subscribe immediately if no api_token is provided - public channels need no token
            await self.subscribe(subscriptions)

        async for raw_message in self.connection:
            LOG.debug(">>> %s", raw_message)
            json_message = json.loads(raw_message)
            # Subscribe only after authentication confirmation
            if json_message["type"] == "AUTHENTICATED":
                LOG.debug("Successfully authenticated! Subscribe now.")
                await self.subscribe(subscriptions)
            elif when_connected.done() is False and json_message["type"] == "SUBSCRIPTIONS" \
                    and subscriptions is not None:
                # Complete start on subscription confirmation message
                when_connected.set_result("Connected with subscriptions")
            elif json_message["type"] == "ERROR":
                LOG.error("!!! %s", json_message)
            # Forward all events
            await self.callback(json_message)

    def get_auth_message_as_json(self):
        """Creates a valid authenticate message with the provided api key"""
        return json.dumps({
            "type": "AUTHENTICATE",
            "api_token": self.api_token
        })

    async def subscribe(self, subscriptions: Subscriptions):
        """Subscribes to the provided websocket channels"""
        if subscriptions is not None:
            subscribe_message = subscriptions.as_json()
            await self.send_message(subscribe_message)

    async def close(self):
        """Closes the websocket connection"""
        if self.connection is not None:
            await self.connection.close()
            self.connection = None
        else:
            LOG.error("No Connection...")

    async def unsubscribe(self, unsubscription: Unsubscription):
        """Unsubscribe from websocket channel(s)"""
        await self.send_message(unsubscription.as_json())

    async def create_order(self, order: CreateOrder):
        """Creates an order via orders channel"""
        await self.send_message(order.to_json())

    async def cancel_order(self, cancel: typing.Union[CancelOrderByOrderId, CancelOrderByClientId]):
        """Cancels an order via orders channel"""
        await self.send_message(cancel.as_json())

    async def send_message(self, message: json):
        """Sends a message to the open websocket connection"""
        if self.connection is not None:
            LOG.debug("Send %s", message)
            await self.connection.send(message)
        else:
            LOG.error("No Connection...")
