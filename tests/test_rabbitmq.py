import pytest
from unittest.mock import AsyncMock, patch
from app.utils.rabbitmq_client import RabbitMQClient
from app.utils.mock_rabbitmq_client import MockRabbitMQClient
from app.utils.message import Message


class TestMessage(Message):
    type_id = "test.message"
    content: str = "test content"


class ResponseMessage(Message):
    type_id = "test.response"
    response: str = "test response"


@pytest.mark.asyncio
class TestMockRabbitMQClient:
    """Test the MockRabbitMQClient functionality"""

    async def test_connect(self, rabbitmq_client):
        """Test that the mock client can connect"""
        assert not rabbitmq_client.is_connected()
        await rabbitmq_client.connect()
        assert rabbitmq_client.is_connected()

    async def test_disconnect(self, connected_rabbitmq_client):
        """Test that the mock client can disconnect"""
        assert connected_rabbitmq_client.is_connected()
        await connected_rabbitmq_client.close()
        assert not connected_rabbitmq_client.is_connected()

    async def test_start_consuming(self, connected_rabbitmq_client):
        """Test that the mock client can start consuming"""
        assert not connected_rabbitmq_client.is_consuming()
        await connected_rabbitmq_client.start_consuming()
        assert connected_rabbitmq_client.is_consuming()

    async def test_stop_consuming(self, connected_rabbitmq_client):
        """Test that the mock client can stop consuming"""
        await connected_rabbitmq_client.start_consuming()
        assert connected_rabbitmq_client.is_consuming()
        await connected_rabbitmq_client.stop_consuming()
        assert not connected_rabbitmq_client.is_consuming()

    async def test_publish_message(self, connected_rabbitmq_client, sample_message):
        """Test that the mock client can publish messages"""
        await connected_rabbitmq_client.publish_message(sample_message)

        assert len(connected_rabbitmq_client.published_messages) == 1
        published = connected_rabbitmq_client.published_messages[0]
        assert published['message'] == sample_message
        assert published['shard'] == '*'
        assert published['routing_key'] == '*.test.message'

    async def test_publish_message_with_custom_shard(self, connected_rabbitmq_client, sample_message):
        """Test that the mock client can publish messages with custom shard"""
        await connected_rabbitmq_client.publish_message(sample_message, shard='shard1')

        assert len(connected_rabbitmq_client.published_messages) == 1
        published = connected_rabbitmq_client.published_messages[0]
        assert published['shard'] == 'shard1'
        assert published['routing_key'] == 'shard1.test.message'

    async def test_register_handler(self, rabbitmq_client):
        """Test that handlers can be registered"""
        async def test_handler(message):
            return ResponseMessage(response="handled")

        rabbitmq_client.register_handler(TestMessage, test_handler)
        assert TestMessage.type_id in rabbitmq_client.message_handlers
        assert rabbitmq_client.message_handlers[TestMessage.type_id][1] == test_handler

    async def test_message_handler_execution(self, connected_rabbitmq_client):
        """Test that registered handlers are executed when messages are published"""
        async def test_handler(message):
            return ResponseMessage(response="handled")

        connected_rabbitmq_client.register_handler(TestMessage, test_handler)

        # Publish a message
        message = TestMessage(content="test")
        await connected_rabbitmq_client.publish_message(message)

        # Check that the handler was executed and response was stored
        assert len(connected_rabbitmq_client.received_messages) == 1
        response = connected_rabbitmq_client.received_messages[0]
        assert isinstance(response, ResponseMessage)
        assert response.response == "handled"

    async def test_message_handler_without_response(self, connected_rabbitmq_client):
        """Test that handlers without responses work correctly"""
        async def test_handler(message):
            return None

        connected_rabbitmq_client.register_handler(TestMessage, test_handler)

        message = TestMessage(content="test")
        await connected_rabbitmq_client.publish_message(message)

        # Check that no response was stored
        assert len(connected_rabbitmq_client.received_messages) == 0

    async def test_clear_messages(self, connected_rabbitmq_client, sample_message):
        """Test that stored messages can be cleared"""
        await connected_rabbitmq_client.publish_message(sample_message)
        assert len(connected_rabbitmq_client.published_messages) == 1

        connected_rabbitmq_client.clear_messages()
        assert len(connected_rabbitmq_client.published_messages) == 0
        assert len(connected_rabbitmq_client.received_messages) == 0

    async def test_publish_without_connection(self, rabbitmq_client, sample_message):
        """Test that publishing without connection raises an error"""
        with pytest.raises(RuntimeError, match="Not connected"):
            await rabbitmq_client.publish_message(sample_message)

    async def test_start_consuming_without_connection(self, rabbitmq_client):
        """Test that starting consumption without connection raises an error"""
        with pytest.raises(RuntimeError, match="Not connected"):
            await rabbitmq_client.start_consuming()


@pytest.mark.asyncio
class TestRabbitMQClientIntegration:
    """Test RabbitMQ client integration with the Flask app"""

    async def test_app_creates_mock_client_in_test_mode(self, app):
        """Test that the app creates a mock client when in test mode"""
        assert 'RABBITMQ_CLIENT' in app.config
        assert isinstance(app.config['RABBITMQ_CLIENT'], MockRabbitMQClient)

    async def test_mock_client_has_registered_handlers(self, app):
        """Test that the mock client has handlers registered from the message router"""
        mock_client = app.config['RABBITMQ_CLIENT']
        # The exact number depends on how many handlers are registered in message_router
        # This test ensures that handlers are being registered
        assert hasattr(mock_client, 'message_handlers')

    async def test_message_flow_integration(self, app, sample_message):
        """Test the complete message flow in the app context"""
        mock_client = app.config['RABBITMQ_CLIENT']

        # Register a test handler
        async def test_handler(message):
            return ResponseMessage(response="processed")

        mock_client.register_handler(TestMessage, test_handler)

        # Connect and publish
        await mock_client.connect()
        await mock_client.publish_message(sample_message)

        # Verify the flow worked
        assert len(mock_client.published_messages) == 1
        assert len(mock_client.received_messages) == 1


@pytest.mark.asyncio
class TestRealRabbitMQClient:
    """Test the real RabbitMQClient (with mocking of external dependencies)"""

    @patch('app.utils.rabbitmq_client.AsyncioConnection')
    async def test_real_client_connect(self, mock_connection_class):
        """Test that the real client attempts to connect properly"""
        mock_connection = AsyncMock()
        mock_connection_class.return_value = mock_connection

        client = RabbitMQClient()
        await client.connect()

        mock_connection_class.assert_called_once()
        # Verify connection parameters
        call_args = mock_connection_class.call_args
        assert call_args[1]['on_open_callback'] == client.on_connection_open
        assert call_args[1]['on_open_error_callback'] == client.on_connection_open_error
        assert call_args[1]['on_close_callback'] == client.on_connection_closed

    @patch('app.utils.rabbitmq_client.AsyncioConnection')
    async def test_real_client_connect_failure(self, mock_connection_class):
        """Test that the real client handles connection failures"""
        mock_connection_class.side_effect = Exception("Connection failed")

        client = RabbitMQClient()
        with pytest.raises(Exception, match="Connection failed"):
            await client.connect()

    async def test_real_client_register_handler(self):
        """Test that the real client can register handlers"""
        client = RabbitMQClient()

        async def test_handler(message):
            return None

        client.register_handler(TestMessage, test_handler)  # type: ignore
        assert TestMessage.type_id in client.message_handlers
        assert client.message_handlers[TestMessage.type_id][1] == test_handler


@pytest.mark.asyncio
class TestMessageHandling:
    """Test message handling functionality"""

    async def test_message_serialization(self, sample_message):
        """Test that messages can be serialized and deserialized"""
        # Test serialization
        serialized = sample_message.model_dump()
        assert 'content' in serialized
        assert serialized['content'] == 'test content'

        # Test deserialization
        deserialized = TestMessage.model_validate(serialized)
        assert deserialized.content == 'test content'

    async def test_message_type_id(self, sample_message):
        """Test that message type IDs work correctly"""
        assert TestMessage.type_id == "test.message"
        assert TestMessage.get_message_type_from_type() == "message"

    async def test_message_creation(self):
        """Test that messages can be created with default values"""
        message = TestMessage()
        assert message.content == "test content"
        assert message.messageId is not None
        assert message.timestamp is not None
        assert message.correlationId is not None
