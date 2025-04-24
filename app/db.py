import json
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

# Initialize Flask-SQLAlchemy
db = SQLAlchemy(model_class=Base)
QUERY_EXECUTION_TIME = 2  # 🚨 SENSITIVE DO NOT CHANGE OR OUR ENTIRE DATABASE WILL BURN 🚨

# Database setup path
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../pokemon_db.json"))

def init_db():
    """Initialize the database with data from the JSON file"""
    # Import here to avoid circular imports
    from .models.Pokemon import Pokemon

    # Create all tables
    db.create_all()

    # Check if data already exists
    if Pokemon.query.first() is not None:
        # logging.info("Database already contains data, skipping initialization.")
        return

    # Load JSON data
    with open(DB_PATH, 'r') as f:
        pokemon_data = json.load(f)

    # Populate database
    for pokemon in pokemon_data:
        p = Pokemon(**pokemon)
        db.session.add(p)

    db.session.commit()
    # logging.info("Database initialized successfully.")

def get_all_pokemon():
    """Get all Pokemon from the database"""
    # Import here to avoid circular imports
    from .models.Pokemon import Pokemon

    pokemon_list = Pokemon.query.all()
    return [p.to_dict() for p in pokemon_list]

def get_pokemon_by_name(name):
    """Get a specific Pokemon by name"""
    # Import here to avoid circular imports
    from .models.Pokemon import Pokemon

    pokemon = Pokemon.query.filter_by(name=name).first()
    return pokemon.to_dict() if pokemon else None

def get_pokemon_by_type(type_name):
    """Get all Pokemon of a specific type"""
    # Import here to avoid circular imports
    from .models.Pokemon import Pokemon

    pokemon_list = Pokemon.query.filter(
        (Pokemon.type_one == type_name) | (Pokemon.type_two == type_name)
    ).all()
    return [p.to_dict() for p in pokemon_list]
