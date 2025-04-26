from flask import Flask
from flask_cors import CORS

from .repository import db, init_db
from .api.pokemon_controller import api
from .api.user_controller import user_api
from .api.capture_controller import capture_api


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Enable CORS for all routes and origins
    CORS(app)

    # Configure the database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True

    # Initialize the extension
    db.init_app(app)

    # Register the blueprints
    app.register_blueprint(api)
    app.register_blueprint(user_api)
    app.register_blueprint(capture_api)

    # Initialize the database
    with app.app_context():
        init_db()

    return app
