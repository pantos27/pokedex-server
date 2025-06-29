# RabbitMQ Testing Infrastructure

This document describes the testing infrastructure for RabbitMQ functionality in the Pokedex application.

## Overview

The testing infrastructure provides a complete mock implementation of the RabbitMQ client that allows you to test message handling, publishing, and consumption without requiring a real RabbitMQ server.

## Key Components

### 1. MockRabbitMQClient

A mock implementation of the RabbitMQ client that:
- Simulates connection management
- Stores published messages for verification
- Executes registered message handlers
- Provides testing utilities for message inspection

### 2. Test Fixtures

The following fixtures are available in `tests/conftest.py`:

- `rabbitmq_client`: Get the mock RabbitMQ client from the app config
- `connected_rabbitmq_client`: Get a connected mock RabbitMQ client
- `event_loop`: Create an event loop for async tests
- `sample_message`: Create a sample test message

### 3. Test Helpers

Located in `tests/test_helpers.py`:

- `TestMessage`, `ResponseMessage`, `ErrorMessage`: Test message classes
- `create_test_handler()`: Create test message handlers
- `wait_for_messages()`: Wait for expected number of messages
- `assert_message_published()`: Assert a message was published
- `assert_message_received()`: Assert a message was received
- `RabbitMQTestScenario`: Helper class for complex test scenarios

## Basic Usage

### Simple Message Test

```python
import pytest
from tests.test_helpers import TestMessage, ResponseMessage

@pytest.mark.asyncio
async def test_simple_message(connected_rabbitmq_client):
    # Register a handler
    async def echo_handler(message: TestMessage):
        return ResponseMessage(response=f"Echo: {message.content}")
    
    connected_rabbitmq_client.register_handler(TestMessage, echo_handler)  # type: ignore
    
    # Publish a message
    message = TestMessage(content="Hello")
    await connected_rabbitmq_client.publish_message(message)
    
    # Verify results
    assert len(connected_rabbitmq_client.published_messages) == 1
    assert len(connected_rabbitmq_client.received_messages) == 1
    assert connected_rabbitmq_client.received_messages[0].response == "Echo: Hello"
```

### Testing with App Context

```python
@pytest.mark.asyncio
async def test_with_app_context(app):
    # Get the mock client from the app
    mock_client = app.config['RABBITMQ_CLIENT']
    
    # Your test logic here
    await mock_client.connect()
    # ... test code ...
```

### Using Test Scenarios

```python
@pytest.mark.asyncio
async def test_complex_scenario(rabbitmq_client):
    scenario = RabbitMQTestScenario(rabbitmq_client)
    
    # Set up handlers
    await scenario.add_handler(TestMessage, ResponseMessage(response="Processed"))
    
    # Connect and test
    await rabbitmq_client.connect()
    try:
        responses = await scenario.publish_and_wait(
            TestMessage(content="test"), 
            expected_responses=1
        )
        assert len(responses) == 1
    finally:
        await rabbitmq_client.close()
        scenario.clear_all()
```

## Advanced Testing Patterns

### 1. Testing Error Scenarios

```python
async def test_handler_error(connected_rabbitmq_client):
    async def error_handler(message: TestMessage):
        raise Exception("Handler failed")
    
    connected_rabbitmq_client.register_handler(TestMessage, error_handler)  # type: ignore
    
    # Publish message that will cause error
    await connected_rabbitmq_client.publish_message(TestMessage(content="will fail"))
    
    # Verify message was published but no response generated
    assert len(connected_rabbitmq_client.published_messages) == 1
    assert len(connected_rabbitmq_client.received_messages) == 0
```

### 2. Testing Concurrent Processing

```python
async def test_concurrent_processing(connected_rabbitmq_client):
    async def slow_handler(message: TestMessage):
        await asyncio.sleep(0.1)
        return ResponseMessage(response=f"Processed: {message.content}")
    
    connected_rabbitmq_client.register_handler(TestMessage, slow_handler)  # type: ignore
    
    # Publish multiple messages concurrently
    messages = [TestMessage(content=f"msg_{i}") for i in range(5)]
    await asyncio.gather(*[
        connected_rabbitmq_client.publish_message(msg) for msg in messages
    ])
    
    # Wait for processing
    await asyncio.sleep(0.5)
    
    # Verify all messages processed
    assert len(connected_rabbitmq_client.received_messages) == 5
```

### 3. Testing Custom Shards

```python
async def test_custom_shards(connected_rabbitmq_client):
    await connected_rabbitmq_client.publish_message(
        TestMessage(content="msg1"), 
        shard="shard1"
    )
    
    published = connected_rabbitmq_client.published_messages[0]
    assert published['shard'] == "shard1"
    assert published['routing_key'] == "shard1.test.message"
```

## Configuration

### Pytest Configuration

The `pytest.ini` file is configured with:

```ini
[pytest]
asyncio_mode = auto
addopts = --verbose --cov=app --cov-report=term-missing --cov-report=html
```

### App Configuration

When the Flask app is created with `test=True`, it automatically:
- Uses `MockRabbitMQClient` instead of `RabbitMQClient`
- Registers all message handlers from the message router
- Stores the mock client in `app.config['RABBITMQ_CLIENT']`

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Only RabbitMQ Tests
```bash
pytest tests/test_rabbitmq.py
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test
```bash
pytest tests/test_rabbitmq.py::TestMockRabbitMQClient::test_connect
```

## Best Practices

1. **Always use the `connected_rabbitmq_client` fixture** for tests that need a connected client
2. **Clear messages between tests** using `client.clear_messages()`
3. **Use type ignore comments** when registering handlers to avoid type issues
4. **Test both success and error scenarios** for robust testing
5. **Use the test helpers** for common assertions and utilities
6. **Test message serialization** to ensure data integrity
7. **Test concurrent scenarios** to catch race conditions

## Troubleshooting

### Common Issues

1. **Type Errors**: Use `# type: ignore` when registering handlers
2. **Async Test Failures**: Ensure tests are marked with `@pytest.mark.asyncio`
3. **Missing Messages**: Use `wait_for_messages()` for async message processing
4. **Connection Issues**: Use the `connected_rabbitmq_client` fixture

### Debug Tips

1. Check `client.published_messages` to see what was published
2. Check `client.received_messages` to see handler responses
3. Use `client.clear_messages()` to reset state between tests
4. Add logging to handlers to debug message flow

## Integration with Real RabbitMQ

When testing against a real RabbitMQ server:

1. Use the real `RabbitMQClient` instead of `MockRabbitMQClient`
2. Ensure RabbitMQ server is running and accessible
3. Use proper connection parameters (host, port, credentials)
4. Handle connection failures and reconnection logic
5. Use Docker Compose for local development with RabbitMQ

Example Docker Compose setup:
```yaml
services:
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
``` 