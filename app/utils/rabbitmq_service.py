import asyncio
import logging
from datetime import datetime
from .rabbitmq_client import rabbitmq_client, StatusCheckMessage, SaveUserCommand
from .message_handlers import handle_status_check_message, handle_save_user_message

logger = logging.getLogger(__name__)


class RabbitMQService:
    """Service class for managing RabbitMQ connection and message handling"""
    
    def __init__(self):
        self._loop = None
        self.is_running = False
    
    async def initialize(self):
        """Initialize RabbitMQ connection and set up message handlers"""
        try:
            self._loop = asyncio.get_event_loop()
            
            # Register handlers
            rabbitmq_client.register_handler(
                message_type='StatusCheckMessage',
                message_class=StatusCheckMessage,
                handler=handle_status_check_message,
                has_response=True
            )
            rabbitmq_client.register_handler(
                message_type='SaveUserCommand',
                message_class=SaveUserCommand,
                handler=handle_save_user_message
            )

            await rabbitmq_client.connect()
            logger.info("RabbitMQ service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing RabbitMQ service: {e}")
            return False
    
    async def start_consuming(self):
        """Start consuming messages (no-op, kept for compatibility/logging)"""
        if self.is_running:
            logger.warning("RabbitMQ consumer is already running")
            return
        
        try:
            self.is_running = True
            logger.info("RabbitMQ consumer started (auto-started after queue bind)")
            # No call to rabbitmq_client.start_consuming() needed
            
        except Exception as e:
            logger.error(f"Error starting RabbitMQ consumer: {e}")
            self.is_running = False
    
    async def stop_consuming(self):
        """Stop consuming messages"""
        if not self.is_running:
            return
        
        try:
            self.is_running = False
            await rabbitmq_client.close()
            logger.info("RabbitMQ consumer stopped")
            
        except Exception as e:
            logger.error(f"Error stopping RabbitMQ consumer: {e}")
    
    async def publish_save_user_command(self, user_id: str, user_name: str, email: str):
        """Publish a save user command"""
        try:
            message = {
                'user_id': user_id,
                'user_name': user_name,
                'email': email,
                'timestamp': datetime.now().isoformat()
            }
            
            await rabbitmq_client.publish_message(
                exchange=rabbitmq_client.exchange_name,
                routing_key="pokedex.SaveUserCommand",
                message=message,
                message_type='SaveUserCommand'
            )
        except Exception as e:
            logger.error(f"Error publishing save user command: {e}")


# Global RabbitMQ service instance
rabbitmq_service = RabbitMQService() 