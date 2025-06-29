"""
Test helpers for RabbitMQ testing
"""
import asyncio
from typing import Optional
from app.utils.message import Message
from app.utils.mock_rabbitmq_client import MockRabbitMQClient


class TestMessage(Message):
    """A test message class for testing purposes"""
    type_id = "test.message"
    content: str = "test content"


class ResponseMessage(Message):
    """A test response message class for testing purposes"""
    type_id = "test.response"
    response: str = "test response"


class ErrorMessage(Message):
    """A test error message class for testing purposes"""
    type_id = "test.error"
    error: str = "test error"


async def create_test_handler(response_message: Optional[Message] = None, should_raise: bool = False):
    """Create a test message handler for testing purposes"""
    async def handler(message: Message):
        if should_raise:
            raise Exception("Test handler error")
        return response_message
    return handler


async def wait_for_messages(client: MockRabbitMQClient, expected_count: int, timeout: float = 1.0):
    """Wait for a specific number of messages to be received"""
    start_time = asyncio.get_event_loop().time()
    while len(client.received_messages) < expected_count:
        if asyncio.get_event_loop().time() - start_time > timeout:
            raise TimeoutError(f"Expected {expected_count} messages, got {len(client.received_messages)}")
        await asyncio.sleep(0.01)


def assert_message_published(client: MockRabbitMQClient, message_type: str, shard: str = '*'):
    """Assert that a specific message was published"""
    for published in client.published_messages:
        if (published['message'].__class__.type_id == message_type and
            published['shard'] == shard):
            return published
    raise AssertionError(f"Message of type {message_type} with shard {shard} not found in published messages")


def assert_message_received(client: MockRabbitMQClient, message_type: str):
    """Assert that a specific message was received"""
    for received in client.received_messages:
        if received.__class__.type_id == message_type:
            return received
    raise AssertionError(f"Message of type {message_type} not found in received messages")


class RabbitMQTestScenario:
    """Helper class for setting up complex RabbitMQ test scenarios"""

    def __init__(self, client: MockRabbitMQClient):
        self.client = client
        self.handlers = []

    async def add_handler(self, message_class: type, response_message: Optional[Message] = None, should_raise: bool = False):
        """Add a handler to the test scenario"""
        handler = await create_test_handler(response_message, should_raise)
        self.client.register_handler(message_class, handler)  # type: ignore
        self.handlers.append((message_class, handler))
        return handler

    async def publish_and_wait(self, message: Message, expected_responses: int = 0, timeout: float = 1.0):
        """Publish a message and wait for responses"""
        initial_count = len(self.client.received_messages)
        await self.client.publish_message(message)

        if expected_responses > 0:
            await wait_for_messages(self.client, initial_count + expected_responses, timeout)

        return self.client.received_messages[initial_count:]

    def clear_all(self):
        """Clear all messages and handlers"""
        self.client.clear_messages()
        self.handlers.clear()


async def run_rabbitmq_test_scenario(test_func, client: MockRabbitMQClient):
    """Decorator to run a test scenario with proper setup and teardown"""
    await client.connect()
    try:
        await test_func(client)
    finally:
        await client.close()
        client.clear_messages()
