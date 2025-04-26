import os
import pytest
from app.repository import db, init_db

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