import logging
import uuid
from typing import Dict, Any, ClassVar
import datetime

from pydantic import BaseModel, Field

from .message_router import MessageRouter

logger = logging.getLogger(__name__)


generate_uuid = lambda: str(uuid.uuid4())
get_now = lambda : datetime.datetime.now(datetime.UTC)


class Message(BaseModel):
    type_id: ClassVar[str]

    @classmethod
    def get_message_type_from_type(cls) -> str:
        return cls.type_id.split('.')[-1]

    messageType: str = "some message type"
    messageId: str = Field(default_factory=generate_uuid)
    timestamp: datetime.datetime = Field(default_factory=get_now)
    correlationId: str = Field(default_factory=generate_uuid)


class StatusCheckMessage(Message):
    """Status check message structure"""
    type_id = 'com.dropit.StatusCheckMessage'
    timestamp: str
    request_id: int
    source: str


class SaveUserCommand(Message):
    """Save user command message structure"""
    type_id = 'com.dropit.SaveUserCommand'
    user_id: str
    user_name: str
    email: str
    timestamp: str



router = MessageRouter()

@router.message_handler(StatusCheckMessage, has_response=True)
async def handle_status_check_message(message: StatusCheckMessage) -> Dict[str, Any]:
    """
    Handle status check messages and return a response

    Args:
        message: StatusCheckMessage object containing the status check request

    Returns:
        Dict containing the status response
    """
    try:
        logger.info(f"Processing status check for request_id: {message.request_id}")

        # Perform status check logic here
        # This could include checking database connectivity, external services, etc.

        response = {
            'status': 'healthy',
            'request_id': message.request_id,
            'source': message.source,
            'timestamp': datetime.datetime.now().isoformat(),
            'services': {
                'database': 'connected',
                'api': 'running',
                'rabbitmq': 'connected'
            },
            'version': '1.0.0'
        }

        logger.info(f"Status check completed for request_id: {message.request_id}")
        return response

    except Exception as e:
        logger.error(f"Error during status check: {e}")
        return {
            'status': 'error',
            'request_id': message.request_id,
            'source': message.source,
            'timestamp': datetime.datetime.now().isoformat(),
            'error': str(e)
        }


@router.message_handler(SaveUserCommand)
async def handle_save_user_message(message: SaveUserCommand):
    """
    Handle save user command messages

    Args:
        message: SaveUserCommand object containing user data to save
    """
    try:
        logger.info(f"Processing save user command for user_id: {message.user_id}")

        # Create user using the existing repository
        user_data = {
            'user_name': message.user_name,
            'email': message.email
        }

        # Note: This would need to be adapted based on your actual user creation logic
        # The current create_user function expects just a user_name, so we'll need to extend it
        # or create a new function that handles the full user data

        # For now, we'll log the user data
        logger.info(f"User data to save: {user_data}")
        if message.user_id == '23425':
            raise RuntimeError("doink")


    except Exception as e:
        logger.error(f"Error during save user command: {e}")
        raise e
        # You might want to publish an error message back to the exchange
        # or handle the error in some other way
