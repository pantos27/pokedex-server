import pytest
import asyncio
from app.repository import db


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    from app import create_app
    app = create_app(test=True)

    yield app

    # Clean up / reset resources
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()


@pytest.fixture
def rabbitmq_client(app):
    """Get the mock RabbitMQ client from the app config."""
    return app.config['RABBITMQ_CLIENT']


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def connected_rabbitmq_client(rabbitmq_client):
    """Get a connected mock RabbitMQ client."""
    await rabbitmq_client.connect()
    yield rabbitmq_client
    await rabbitmq_client.close()


@pytest.fixture
def sample_message():
    """Create a sample message for testing."""
    from app.utils.message import Message

    class TestMessage(Message):
        type_id = "test.message"
        content: str = "test content"

    return TestMessage(content="test content")
