import asyncio
import json
import logging
from typing import Callable, Dict, Any, Tuple, Type, Optional

import pika
from dataclasses import fields, is_dataclass, dataclass
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.channel import Channel


logger = logging.getLogger(__name__)


@dataclass
class StatusCheckMessage:
    """Status check message structure"""
    timestamp: str
    request_id: str
    source: str


@dataclass
class SaveUserCommand:
    """Save user command message structure"""
    user_id: str
    user_name: str
    email: str
    timestamp: str


class RabbitMQClient:
    """RabbitMQ client for handling message consumption and publishing"""

    def __init__(self, host='localhost', port=5672, username='guest', password='guest'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._connection: Optional[AsyncioConnection] = None
        self._channel: Optional[Channel] = None
        self._closing = False
        self._consumer_tag = None

        # Exchange and queue names
        self.exchange_name = 'master-exchange'
        self.queue_name = 'master-queue'

        # Message handlers
        self.message_handlers: Dict[str, Tuple[Type, Callable, bool]] = {}

    def register_handler(self, message_type: str, message_class: Type, handler: Callable, has_response: bool = False):
        """Register a handler for a specific message type"""
        if not is_dataclass(message_class):
            raise TypeError("message_class must be a dataclass")
        self.message_handlers[message_type] = (message_class, handler, has_response)

    def _get_credentials(self):
        return pika.PlainCredentials(self.username, self.password)

    async def connect(self):
        """Establish connection to RabbitMQ"""
        if self._connection and self._connection.is_open:
            return
        logger.info(f"Connecting to RabbitMQ at {self.host}:{self.port}")
        try:
            # Directly instantiate AsyncioConnection (do not use loop.create_connection)
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
        logger.info("Attempting to reconnect...")
        await asyncio.sleep(5)
        await self.connect()

    def on_connection_open(self, connection: AsyncioConnection):
        logger.info('Connection opened')
        self._connection = connection
        self.open_channel()

    def on_connection_open_error(self, connection: AsyncioConnection, err):
        logger.error(f'Connection open failed: {err}')
        asyncio.get_running_loop().create_task(self.reconnect())

    def on_connection_closed(self, connection: AsyncioConnection, reason):
        logger.warning(f'Connection closed: {reason}')
        self._connection = None
        self._channel = None
        if not self._closing:
            asyncio.get_running_loop().create_task(self.reconnect())

    def open_channel(self):
        logger.info('Creating a new channel')
        if self._connection:
            self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel: Channel):
        logger.info('Channel opened')
        self._channel = channel
        self.setup_exchange()
        # Do NOT start consuming here; wait until after queue is bound

    def setup_exchange(self):
        logger.info(f'Declaring exchange: {self.exchange_name}')
        if self._channel:
            self._channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='topic',
                durable=True,
                callback=self.on_exchange_declareok
            )

    def on_exchange_declareok(self, frame):
        logger.info('Exchange declared')
        self.setup_queue()

    def setup_queue(self):
        logger.info(f'Declaring queue: {self.queue_name}')
        if self._channel:
            self._channel.queue_declare(
                queue=self.queue_name,
                durable=True,
                callback=self.on_queue_declareok
            )

    def on_queue_declareok(self, frame):
        logger.info('Queue declared')
        self.bind_queues()

    def bind_queues(self):
        if not self.message_handlers:
            logger.warning("No message handlers registered. Binding queue with '#' to receive all messages.")
            routing_key = '#'
            if self._channel:
                self._channel.queue_bind(
                    self.queue_name,
                    self.exchange_name,
                    routing_key=routing_key,
                    callback=self.on_bindok
                )
        else:
            for message_type in self.message_handlers.keys():
                routing_key = f"*.{message_type}"
                logger.info(f"Binding queue {self.queue_name} to exchange {self.exchange_name} with routing key {routing_key}")
                if self._channel:
                    self._channel.queue_bind(
                        self.queue_name,
                        self.exchange_name,
                        routing_key=routing_key,
                        callback=self.on_bindok
                    )

    def on_bindok(self, _):
        logger.info('Queue bound')
        self._start_consuming()

    def _start_consuming(self):
        if self._consumer_tag:
            return
        logger.info("Starting consumer")
        if self._channel:
            self._channel.basic_qos(prefetch_count=1)
            def on_message_wrapper(channel, basic_deliver, properties, body):
                asyncio.get_running_loop().create_task(
                    self.on_message(channel, basic_deliver, properties, body)
                )
            self._consumer_tag = self._channel.basic_consume(
                self.queue_name, on_message_wrapper
            )

    async def stop_consuming(self):
        if self._consumer_tag and self._channel:
            logger.info("Stopping consumer")
            self._channel.basic_cancel(self._consumer_tag, self.on_cancelok)
            self._consumer_tag = None

    def on_cancelok(self, frame):
        logger.info('Consumer cancelled')
        self.close_channel()

    async def on_message(self, channel, basic_deliver, properties, body):
        message_type = properties.headers.get('__TypeId__')
        try:
            message_data = json.loads(body.decode('utf-8'))
            routing_key = basic_deliver.routing_key
            logger.info(f"Received message with routing key: {routing_key}, type: {message_type}")

            if message_type in self.message_handlers:
                message_class, handler, has_response = self.message_handlers[message_type]
                try:
                    constructor_args = {field.name: message_data.get(field.name) for field in fields(message_class)}
                    message_obj = message_class(**constructor_args)
                    response = await handler(message_obj)

                    if has_response:
                        if response is not None:
                            response_routing_key = f"{routing_key.split('.')[0]}.{message_type}Response"
                            await self.publish_message(
                                exchange=self.exchange_name,
                                routing_key=response_routing_key,
                                message=response,
                                message_type=f'{message_type}Response'
                            )
                        else:
                            logger.error(f"Handler for {message_type} was supposed to return a response but returned None.")
                    if self._channel:
                        self._channel.basic_ack(delivery_tag=basic_deliver.delivery_tag)

                except Exception as e:
                    logger.error(f"Error processing message type {message_type}: {e}. Re-queueing message.")
                    if self._channel:
                        self._channel.basic_nack(delivery_tag=basic_deliver.delivery_tag, requeue=True)
                    raise
            else:
                logger.warning(f"Unknown message type: {message_type}")
                if self._channel:
                    self._channel.basic_ack(delivery_tag=basic_deliver.delivery_tag)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message with type {message_type}: {e}. Discarding message.")
            if self._channel:
                self._channel.basic_ack(delivery_tag=basic_deliver.delivery_tag)
        except Exception as e:
            logger.error(f"Unexpected error in on_message for type {message_type}: {e}")
            if self._channel:
                self._channel.basic_nack(delivery_tag=basic_deliver.delivery_tag, requeue=True)
            raise

    async def publish_message(self, exchange: str, routing_key: str, message: Dict[str, Any], message_type: str = ''):
        if not self._channel or not self._channel.is_open:
            logger.error("Cannot publish message, channel is not available.")
            return

        try:
            message_body = json.dumps(message).encode('utf-8')
            properties = pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json',
                headers={'__TypeId__': message_type} if message_type else {}
            )
            if self._channel:
                self._channel.basic_publish(
                    exchange=exchange,
                    routing_key=routing_key,
                    body=message_body,
                    properties=properties
                )
            logger.info(f"Published message to {exchange} with routing key: {routing_key}, type: {message_type}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")

    def close_channel(self):
        if self._channel:
            logger.info('Closing the channel')
            self._channel.close()

    async def close(self):
        if not self._closing:
            self._closing = True
            logger.info('Closing connection')
            if self._connection and self._connection.is_open:
                await self.stop_consuming()
                self._connection.close()


rabbitmq_client = RabbitMQClient()
