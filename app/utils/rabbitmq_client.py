import asyncio
import json
import logging
from asyncio import InvalidStateError
from typing import Dict, Tuple, Type, Optional

import pika
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.channel import Channel

from app.utils.message import Message
from app.utils.rabbitmq_service import RabbitMQService, MessageHandler, MessageSubType

logger = logging.getLogger(__name__)


class RabbitMQClient(RabbitMQService):
    """RabbitMQ client for handling message consumption and publishing"""

    def __init__(self, host='localhost', port=5672, username='guest', password='guest'):
        self._pending_binds_set = set()
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
        self.message_handlers: Dict[str, Tuple[Type[MessageSubType], MessageHandler]] = {}

    def register_handler(self, message_class: Type[MessageSubType], handler: MessageHandler):
        """Register a handler for a specific message type"""
        self.message_handlers[message_class.type_id] = (message_class, handler)

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
            routing_keys = [f"*.{message_class.get_message_type_from_type()}" for message_class, _ in
                            self.message_handlers.values()]
            self._pending_binds_set = set(routing_keys)
            for routing_key in routing_keys:
                logger.debug(
                    f"Binding queue {self.queue_name} to exchange {self.exchange_name} with routing key {routing_key}")
                if self._consume_channel:
                    self._consume_channel.queue_bind(
                        self.queue_name,
                        self.exchange_name,
                        routing_key=routing_key,
                        callback=lambda _frame, rk=routing_key: self.on_bind_ok(_frame, rk)
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
                message_class, handler = self.message_handlers[message_type]

                message = message_class.model_validate_json(body.decode('utf-8'))

                result = await handler(message)  # type: ignore

                channel.basic_ack(delivery_tag=basic_deliver.delivery_tag)

                # If the handler returns a response message, publish it
                if result:
                    await self.publish_message(result)

            else:
                logger.warning(f"consumed bus message [{message_type}] from queue [{self.queue_name}] which is not in the subscription list")
                # Reject the message and don't requeue it
                channel.basic_ack(delivery_tag=basic_deliver.delivery_tag)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Reject the message and requeue it
            channel.basic_nack(delivery_tag=basic_deliver.delivery_tag, requeue=True)
            raise

    async def publish_message(self, message: Message, shard: str = '*'):
        """Publish a message to RabbitMQ"""
        if not self._publish_channel or not self._publish_channel.is_open:
            logger.error("Publish channel not available")
            return

        try:
            routing_key = f"{shard}.{message.__class__.get_message_type_from_type()}"
            message_body = json.dumps(message.model_dump()).encode('utf-8')

            properties = pika.BasicProperties(
                content_type='application/json',
                headers={'__TypeId__': message.__class__.type_id}
            )

            self._publish_channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=message_body,
                properties=properties
            )

            logger.info(f"Published message: {message.__class__.__name__} with routing key: {routing_key}")

        except Exception as e:
            logger.error(f"Error publishing message: {e}")

    def close_channel(self):
        """Close the publish channel"""
        self.close_publish_channel()

    async def close(self):
        """Close the connection and stop consuming"""
        self._closing = True
        await self.stop_consuming()
        self.close_consume_channel()
        self.close_publish_channel()
        if self._connection:
            self._connection.close()


# Global instance for the application
rabbitmq_client = RabbitMQClient()
