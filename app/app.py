from flask import Flask
from flask_cors import CORS

from .repository import db, init_db
from .api.controller import api


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

    # Register the blueprint
    app.register_blueprint(api)

    # Initialize the database
    with app.app_context():
        init_db()

    return app
