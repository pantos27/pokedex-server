import logging
from abc import ABC, abstractmethod
from typing import Type, Callable, Awaitable, Optional, NewType

from utils.message import Message

logger = logging.getLogger(__name__)

MessageSubType = NewType("MessageSubType", Message)
type MessageHandler = Callable[[MessageSubType], Awaitable[Optional[Message]]]

class RabbitMQService(ABC):
    """Service class for managing RabbitMQ connection and message handling"""

    @abstractmethod
    async def connect(self):
        """Initialize RabbitMQ connection and set up message handlers"""
        pass

    async def close(self):
        """Stop consuming messages"""
        pass

    def register_handler(self, message_class: Type[MessageSubType],
                         handler: MessageHandler):
        """Register a handler for a specific message type"""
        pass

    async def publish_message(self, message: Message, shard: str = '*'):
        """Publish a save user command"""
        pass
