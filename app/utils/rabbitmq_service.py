import logging
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class RabbitMQService(ABC):
    """Service class for managing RabbitMQ connection and message handling"""

    @abstractmethod
    async def connect(self):
        """Initialize RabbitMQ connection and set up message handlers"""
        pass

    async def start_consuming(self):
        """Start consuming messages"""
        pass

    async def stop_consuming(self):
        """Stop consuming messages"""
        pass

    async def publish_save_user_command(self, user_id: str, user_name: str, email: str):
        """Publish a save user command"""
        pass


# Global RabbitMQ service instance
# rabbitmq_service: RabbitMQService = rabbitmq_client

