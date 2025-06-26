import logging
from abc import ABC, abstractmethod
from typing import Type, Callable

from utils.message_handlers import Message

logger = logging.getLogger(__name__)


class RabbitMQService(ABC):
    """Service class for managing RabbitMQ connection and message handling"""

    @abstractmethod
    async def connect(self):
        """Initialize RabbitMQ connection and set up message handlers"""
        pass

    async def close(self):
        """Stop consuming messages"""
        pass

    def register_handler(self, message_class: Type[Message], handler: Callable, has_response: bool = False):
        """Register a handler for a specific message type"""
        pass


    async def publish_message(self, user_id: str, user_name: str, email: str):
        """Publish a save user command"""
        pass




