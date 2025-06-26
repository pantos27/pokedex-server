import asyncio
import json
import logging
from asyncio import InvalidStateError
from typing import Callable, Dict, Any, Tuple, Type, Optional, cast

import pika
from pydantic import BaseModel
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.channel import Channel

from utils.rabbitmq_service import RabbitMQService

logger = logging.getLogger(__name__)


class StatusCheckMessage(BaseModel):
    """Status check message structure"""
    timestamp: str
    request_id: int
    source: str


class SaveUserCommand(BaseModel):
    """Save user command message structure"""
    user_id: str
    user_name: str
    email: str
    timestamp: str


class RabbitMQClient(RabbitMQService):
    """RabbitMQ client for handling message consumption and publishing"""

    def __init__(self, host='localhost', port=5672, username='guest', password='guest'):
        self.reconnect_attempts = 0
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._connection: Optional[AsyncioConnection] = None
        self._consume_channel: Optional[Channel] = None
        self._publish_channel: Optional[Channel] = None
        self._closing = False
        self._consumer_tag = None

        # Exchange and queue names
        self.exchange_name = 'master-exchange'
        self.queue_name = 'master-queue'

        # Message handlers
        self.message_handlers: Dict[str, Tuple[Type[BaseModel], Callable, bool]] = {}

    def register_handler(self, message_type: str, message_class: Type, handler: Callable, has_response: bool = False):
        """Register a handler for a specific message type"""
        if not issubclass(message_class, BaseModel):
            raise TypeError("message_class must inherit from pydantic BaseModel")
        self.message_handlers[message_type] = (message_class, handler, has_response)

    def _get_credentials(self):
        return pika.PlainCredentials(self.username, self.password)

    async def connect(self):
        """Establish connection to RabbitMQ"""
        if self._connection and self._connection.is_open:
            return
        logger.info(f"Connecting to RabbitMQ at {self.host}:{self.port}")
        try:
            self._connection = AsyncioConnection(
                pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=self._get_credentials(),
                    heartbeat=600,
                    blocked_connection_timeout=300.0  # type: ignore
                ),
                on_open_callback=self.on_connection_open,
                on_open_error_callback=self.on_connection_open_error,
                on_close_callback=self.on_connection_closed
            )
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            await self.reconnect()

    async def reconnect(self):
        if self.reconnect_attempts < 5:
            logger.info(f"Attempting to reconnect... ({self.reconnect_attempts})")
            self.reconnect_attempts += 1
            await asyncio.sleep(5)
            await self.connect()
        else:
            logger.info("Failed to reconnect")
            asyncio.get_running_loop().call_exception_handler({"message": "Failed to reconnect msg"})

    def on_connection_open(self, connection: AsyncioConnection):
        logger.debug('Connection opened')
        self.reconnect_attempts = 0
        self._connection = connection
        # Open consume channel first, then publish channel
        self._connection.channel(on_open_callback=self.on_consume_channel_open)

    def on_connection_open_error(self, connection: AsyncioConnection, err):
        logger.error(f'Connection open failed: {err}')
        asyncio.get_running_loop().create_task(self.reconnect())

    def on_connection_closed(self, connection: AsyncioConnection, reason):
        logger.warning(f'Connection closed: {reason}')
        self._connection = None
        self._consume_channel = None
        self._publish_channel = None
        self._consumer_tag = None
        if not self._closing:
            asyncio.get_running_loop().create_task(self.reconnect())

    def on_consume_channel_open(self, channel: Channel):
        logger.debug('Consume channel opened')
        self._consume_channel = channel
        if self._consume_channel:
            self._consume_channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='topic',
                durable=True,
                callback=self.on_exchange_declared
            )
        # Open publish channel in parallel, only if connection exists
        if self._connection:
            self._connection.channel(on_open_callback=self.on_publish_channel_open)

    def on_publish_channel_open(self, channel: Channel):
        logger.debug('Publish channel opened')
        self._publish_channel = channel

    def on_exchange_declared(self, frame):
        logger.debug('Exchange declared')
        if self._consume_channel:
            self._consume_channel.queue_declare(
                queue=self.queue_name,
                durable=True,
                callback=self.on_queue_declared
            )

    def on_queue_declared(self, frame):
        logger.debug('Queue declared, creating bindings to exchange')
        if not self.message_handlers:
            logger.exception("No message handlers registered.")
            raise InvalidStateError("No message handlers registered.")
        else:
            routing_keys = [f"*.{message_type}" for message_type in self.message_handlers.keys()]
            self._pending_binds_set = set(routing_keys)
            for routing_key in routing_keys:
                logger.debug(
                    f"Binding queue {self.queue_name} to exchange {self.exchange_name} with routing key {routing_key}")
                if self._consume_channel:
                    self._consume_channel.queue_bind(
                        self.queue_name,
                        self.exchange_name,
                        routing_key=routing_key,
                        callback=lambda frame, rk=routing_key: self.on_bind_ok(frame, rk)
                    )

    def on_bind_ok(self, _, routing_key):
        logger.debug(f'Queue bound for routing key: {routing_key}')
        self._pending_binds_set.discard(routing_key)
        if not self._pending_binds_set:
            self.start_consuming()

    def start_consuming(self):
        if self._consumer_tag:
            return
        logger.info("Starting consumer")
        if self._consume_channel:
            self._consume_channel.basic_qos(prefetch_count=1)

            def on_message_wrapper(channel, basic_deliver, properties, body):
                asyncio.get_running_loop().create_task(
                    self.on_message(channel, basic_deliver, properties, body)
                )

            self._consumer_tag = self._consume_channel.basic_consume(
                self.queue_name, on_message_wrapper
            )

    async def stop_consuming(self):
        if self._consumer_tag and self._consume_channel:
            logger.info("Stopping consumer")
            self._consume_channel.basic_cancel(self._consumer_tag, self.on_cancel_ok)
            self._consumer_tag = None

    def on_cancel_ok(self, frame):
        logger.debug('Consumer cancelled')
        self._consumer_tag = None
        self.close_consume_channel()

    def close_consume_channel(self):
        if self._consume_channel:
            logger.debug('Closing the consume channel')
            self._consume_channel.close()
            self._consume_channel = None
            self._consumer_tag = None

    def close_publish_channel(self):
        if self._publish_channel:
            logger.debug('Closing the publish channel')
            self._publish_channel.close()
            self._publish_channel = None

    async def on_message(self, channel, basic_deliver, properties, body):
        message_type = properties.headers.get('__TypeId__')
        try:
            routing_key = basic_deliver.routing_key
            logger.info(f"Received message with routing key: {routing_key}, type: {message_type}")

            if message_type in self.message_handlers:
                message_class, handler, has_response = self.message_handlers[message_type]
                try:
                    message_obj = message_class.model_validate_json(body)
                    response = await handler(message_obj)

                    if has_response:
                        if response is not None:
                            response_routing_key = f"{routing_key.split('.')[0]}.{message_type}Response"
                            if isinstance(response, BaseModel):
                                response_data = cast(dict, response.model_dump())
                            elif isinstance(response, dict):
                                response_data = response
                            else:
                                logger.error(
                                    f"Handler for {message_type} returned an unsupported response type: {type(response)}")
                                response_data = None
                            if response_data is not None:
                                await self.publish_message(
                                    exchange=self.exchange_name,
                                    routing_key=response_routing_key,
                                    message=response_data,
                                    message_type=f'{message_type}Response'
                                )
                        else:
                            logger.error(
                                f"Handler for {message_type} was supposed to return a response but returned None.")
                    if self._consume_channel:
                        self._consume_channel.basic_ack(delivery_tag=basic_deliver.delivery_tag)

                except Exception as e:
                    logger.error(f"Error processing message type {message_type}: {e}. Re-queueing message.")
                    if self._consume_channel:
                        self._consume_channel.basic_nack(delivery_tag=basic_deliver.delivery_tag, requeue=True)
                    raise
            else:
                logger.warning(f"Unknown message type: {message_type}")
                if self._consume_channel:
                    self._consume_channel.basic_ack(delivery_tag=basic_deliver.delivery_tag)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message with type {message_type}: {e}. Discarding message.")
            if self._consume_channel:
                self._consume_channel.basic_ack(delivery_tag=basic_deliver.delivery_tag)
        except Exception as e:
            logger.error(f"Unexpected error in on_message for type {message_type}: {e}")
            if self._consume_channel:
                self._consume_channel.basic_nack(delivery_tag=basic_deliver.delivery_tag, requeue=True)
            raise

    async def publish_message(self, exchange: str, routing_key: str, message: Dict[str, Any], message_type: str = ''):
        if not self._publish_channel or not self._publish_channel.is_open:
            logger.error("Cannot publish message, publish channel is not available.")
            return

        try:
            if isinstance(message, BaseModel):
                message_body = json.dumps(message.model_dump()).encode('utf-8')
            elif isinstance(message, dict):
                message_body = json.dumps(message).encode('utf-8')
            else:
                logger.error(f"Message to publish is not a dict or BaseModel: {type(message)}")
                return
            properties = pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json',
                headers={'__TypeId__': message_type} if message_type else {}
            )
            if self._publish_channel:
                self._publish_channel.basic_publish(
                    exchange=exchange,
                    routing_key=routing_key,
                    body=message_body,
                    properties=properties
                )
            logger.info(f"Published message to {exchange} with routing key: {routing_key}, type: {message_type}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")

    def close_channel(self):
        self.close_consume_channel()
        self.close_publish_channel()

    async def close(self):
        if not self._closing:
            self._closing = True
            logger.info('Closing connection')
            if self._connection and self._connection.is_open:
                await self.stop_consuming()
                self._connection.close()


rabbitmq_client = RabbitMQClient()

# Decorator for message handler registration
def message_handler(message_type: str, message_class: Type[BaseModel], has_response: bool = False):
    """Decorator to register a function as a message handler."""
    def decorator(func):
        rabbitmq_client.register_handler(
            message_type=message_type,
            message_class=message_class,
            handler=func,
            has_response=has_response
        )
        return func
    return decorator
