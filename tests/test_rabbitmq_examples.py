"""
Example tests demonstrating how to use the RabbitMQ testing infrastructure
"""
import pytest
from tests.test_helpers import (
    TestMessage, ResponseMessage, ErrorMessage,
    RabbitMQTestScenario, assert_message_published,
    assert_message_received
)


@pytest.mark.asyncio
class TestRabbitMQExamples:
    """Example tests showing how to use the RabbitMQ testing infrastructure"""

    async def test_simple_message_flow(self, connected_rabbitmq_client):
        """Example: Simple message publish and handler execution"""
        # Register a handler that returns a response
        async def echo_handler(message: TestMessage):
            return ResponseMessage(response=f"Echo: {message.content}")

        connected_rabbitmq_client.register_handler(TestMessage, echo_handler)  # type: ignore

        # Publish a message
        message = TestMessage(content="Hello, World!")
        await connected_rabbitmq_client.publish_message(message)

        # Verify the message was published
        published = assert_message_published(connected_rabbitmq_client, "test.message")
        assert published['message'].content == "Hello, World!"

        # Verify the response was received
        response = assert_message_received(connected_rabbitmq_client, "test.response")
        assert response.response == "Echo: Hello, World!"

    async def test_multiple_message_types(self, connected_rabbitmq_client):
        """Example: Handling multiple message types with different handlers"""
        # Register handlers for different message types
        async def test_handler(message: TestMessage):
            return ResponseMessage(response="Test processed")

        async def error_handler(message: ErrorMessage):
            return ResponseMessage(response=f"Error handled: {message.error}")

        connected_rabbitmq_client.register_handler(TestMessage, test_handler)  # type: ignore
        connected_rabbitmq_client.register_handler(ErrorMessage, error_handler)  # type: ignore

        # Publish different types of messages
        test_msg = TestMessage(content="test")
        error_msg = ErrorMessage(error="something went wrong")

        await connected_rabbitmq_client.publish_message(test_msg)
        await connected_rabbitmq_client.publish_message(error_msg)

        # Verify both messages were processed
        assert len(connected_rabbitmq_client.published_messages) == 2
        assert len(connected_rabbitmq_client.received_messages) == 2

        # Check specific responses
        responses = connected_rabbitmq_client.received_messages
        assert any(r.response == "Test processed" for r in responses)
        assert any(r.response == "Error handled: something went wrong" for r in responses)

    async def test_message_with_custom_shard(self, connected_rabbitmq_client):
        """Example: Publishing messages with custom shards"""
        async def shard_handler(message: TestMessage):
            return ResponseMessage(response="Shard processed")

        connected_rabbitmq_client.register_handler(TestMessage, shard_handler)  # type: ignore

        # Publish messages with different shards
        await connected_rabbitmq_client.publish_message(TestMessage(content="msg1"), shard="shard1")
        await connected_rabbitmq_client.publish_message(TestMessage(content="msg2"), shard="shard2")

        # Verify shard-specific routing
        shard1_msg = assert_message_published(connected_rabbitmq_client, "test.message", "shard1")
        shard2_msg = assert_message_published(connected_rabbitmq_client, "test.message", "shard2")

        assert shard1_msg['routing_key'] == "shard1.test.message"
        assert shard2_msg['routing_key'] == "shard2.test.message"

    async def test_handler_error_handling(self, connected_rabbitmq_client):
        """Example: Testing handler error scenarios"""
        async def error_handler(message: TestMessage):
            raise Exception("Handler failed")

        connected_rabbitmq_client.register_handler(TestMessage, error_handler)  # type: ignore

        # Publish a message that will cause an error
        message = TestMessage(content="will fail")
        await connected_rabbitmq_client.publish_message(message)

        # Verify the message was published but no response was generated
        assert len(connected_rabbitmq_client.published_messages) == 1
        assert len(connected_rabbitmq_client.received_messages) == 0

    async def test_using_test_scenario_helper(self, rabbitmq_client):
        """Example: Using the RabbitMQTestScenario helper for complex scenarios"""
        scenario = RabbitMQTestScenario(rabbitmq_client)

        # Set up the scenario
        await scenario.add_handler(TestMessage, ResponseMessage(response="Scenario processed"))
        await scenario.add_handler(ErrorMessage, ResponseMessage(response="Error scenario"))

        # Connect and run the scenario
        await rabbitmq_client.connect()

        try:
            # Publish messages and wait for responses
            responses1 = await scenario.publish_and_wait(
                TestMessage(content="scenario test"),
                expected_responses=1
            )

            responses2 = await scenario.publish_and_wait(
                ErrorMessage(error="scenario error"),
                expected_responses=1
            )

            # Verify responses
            assert len(responses1) == 1
            assert responses1[0].response == "Scenario processed"

            assert len(responses2) == 1
            assert responses2[0].response == "Error scenario"

        finally:
            await rabbitmq_client.close()
            scenario.clear_all()

    async def test_message_serialization_roundtrip(self, connected_rabbitmq_client):
        """Example: Testing message serialization and deserialization"""
        # Create a message with custom data
        original_message = TestMessage(content="serialization test")

        # Serialize and deserialize
        serialized = original_message.model_dump()
        deserialized = TestMessage.model_validate(serialized)

        # Verify the roundtrip worked
        assert deserialized.content == original_message.content
        assert deserialized.messageId == original_message.messageId
        assert deserialized.timestamp == original_message.timestamp
        assert deserialized.correlationId == original_message.correlationId

    async def test_concurrent_message_processing(self, connected_rabbitmq_client):
        """Example: Testing concurrent message processing"""
        import asyncio

        # Create a handler that simulates some processing time
        async def slow_handler(message: TestMessage):
            await asyncio.sleep(0.1)  # Simulate processing time
            return ResponseMessage(response=f"Processed: {message.content}")

        connected_rabbitmq_client.register_handler(TestMessage, slow_handler)  # type: ignore

        # Publish multiple messages concurrently
        messages = [
            TestMessage(content=f"msg_{i}")
            for i in range(5)
        ]

        # Publish all messages
        publish_tasks = [
            connected_rabbitmq_client.publish_message(msg)
            for msg in messages
        ]

        await asyncio.gather(*publish_tasks)

        # Wait a bit for processing
        await asyncio.sleep(0.5)

        # Verify all messages were processed
        assert len(connected_rabbitmq_client.published_messages) == 5
        assert len(connected_rabbitmq_client.received_messages) == 5

        # Verify all responses are present
        responses = connected_rabbitmq_client.received_messages
        for i in range(5):
            assert any(f"Processed: msg_{i}" in r.response for r in responses)

    async def test_message_flow_with_app_context(self, app):
        """Example: Testing RabbitMQ integration within the Flask app context"""
        # Get the mock client from the app
        mock_client = app.config['RABBITMQ_CLIENT']

        # Register a test handler
        async def app_handler(message: TestMessage):
            return ResponseMessage(response="App context processed")

        mock_client.register_handler(TestMessage, app_handler)  # type: ignore

        # Connect and publish
        await mock_client.connect()
        await mock_client.publish_message(TestMessage(content="app test"))

        # Verify the flow worked in app context
        assert len(mock_client.published_messages) == 1
        assert len(mock_client.received_messages) == 1
        assert mock_client.received_messages[0].response == "App context processed"

        await mock_client.close()
