import os
import pytest
from app.repository import db, init_db

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    from app import create_app
    app = create_app()
    
    app.config['TESTING'] = True
    
    # Create the database and load test data
    with app.app_context():
        init_db()

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