from typing import Dict, Tuple, Type

from app.utils.message import Message
from app.utils.rabbitmq_client import logger
from app.utils.rabbitmq_service import RabbitMQService, MessageSubType, MessageHandler


class MockRabbitMQClient(RabbitMQService):
    """Mock RabbitMQ client for testing purposes"""

    def __init__(self, host='localhost', port=5672, username='guest', password='guest'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._connected = False
        self._consuming = False

        # Exchange and queue names
        self.exchange_name = 'master-exchange'
        self.queue_name = 'master-queue'

        # Message handlers
        self.message_handlers: Dict[str, Tuple[Type[MessageSubType], MessageHandler]] = {}

        # For testing - store published messages
        self.published_messages = []
        self.received_messages = []

    def register_handler(self, message_class: Type[MessageSubType], handler: MessageHandler):
        """Register a handler for a specific message type"""
        self.message_handlers[message_class.type_id] = (message_class, handler)

    async def connect(self):
        """Mock connection - always succeeds"""
        logger.info(f"Mock connecting to RabbitMQ at {self.host}:{self.port}")
        self._connected = True

    async def start_consuming(self):
        """Mock start consuming - just sets the flag"""
        if not self._connected:
            raise RuntimeError("Not connected")
        self._consuming = True
        logger.info("Mock consumer started")

    async def stop_consuming(self):
        """Mock stop consuming"""
        self._consuming = False
        logger.info("Mock consumer stopped")

    async def publish_message(self, message: Message, shard: str = '*'):
        """Mock publish message - stores the message for testing"""
        if not self._connected:
            raise RuntimeError("Not connected")

        # Store the published message for testing
        self.published_messages.append({
            'message': message,
            'shard': shard,
            'routing_key': f"{shard}.{message.__class__.get_message_type_from_type()}"
        })

        logger.info(f"Mock published message: {message.__class__.__name__} with routing key: {shard}.{message.__class__.get_message_type_from_type()}")

        # Simulate message processing if handlers are registered
        message_type = message.__class__.type_id
        if message_type in self.message_handlers:
            message_class, handler = self.message_handlers[message_type]
            try:
                result = await handler(message)  # type: ignore
                if result:
                    self.received_messages.append(result)
                logger.info(f"Mock message handler executed for type: {message_type}")
            except Exception as e:
                logger.error(f"Mock message handler error: {e}")

    async def close(self):
        """Mock close connection"""
        self._connected = False
        self._consuming = False
        logger.info("Mock connection closed")

    def is_connected(self):
        """Check if mock connection is active"""
        return self._connected

    def is_consuming(self):
        """Check if mock consumer is active"""
        return self._consuming

    def clear_messages(self):
        """Clear stored messages for testing"""
        self.published_messages.clear()
        self.received_messages.clear()
