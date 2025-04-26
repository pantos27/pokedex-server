import logging
import time

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from db import QUERY_EXECUTION_TIME


class Base(DeclarativeBase):
    pass


# Initialize Flask-SQLAlchemy
db = SQLAlchemy(model_class=Base)


def wait():
    from flask import current_app
    if current_app.config.get('TESTING', False):
        time.sleep(0)
    else:
        time.sleep(QUERY_EXECUTION_TIME)


def init_db():
    """Initialize the database with data from the JSON file"""
    # Import here to avoid circular imports
    from app.models.Pokemon import Pokemon
    from app.models.User import User
    from app.models.Captured import Captured

    # Create all tables
    db.create_all()

    # Check if Pokémon data already exists
    if Pokemon.query.first() is not None:
        logging.info("Database already contains Pokemon data, skipping initialization.")
    else:
        # Load JSON data
        from db import get
        pokemon_data = get()

        # Populate database with Pokémon
        for pokemon in pokemon_data:
            p = Pokemon(**pokemon)
            db.session.add(p)

        db.session.commit()
        logging.info("Pokemon data initialized successfully.")