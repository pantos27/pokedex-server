import logging
import time

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from app.utils.PaginatedResponse import PaginatedResponse
from db import QUERY_EXECUTION_TIME


class Base(DeclarativeBase):
    pass


# Initialize Flask-SQLAlchemy
db = SQLAlchemy(model_class=Base)


def wait():
    time.sleep(QUERY_EXECUTION_TIME)


def get_sort(sort_order):
    from .models.Pokemon import Pokemon
    return (
        Pokemon.number.asc() if sort_order.lower() == 'asc' else Pokemon.number.desc()
    )


def init_db():
    """Initialize the database with data from the JSON file"""
    # Import here to avoid circular imports
    from .models.Pokemon import Pokemon
    from .models.User import User

    # Create all tables
    db.create_all()

    # Check if Pokemon data already exists
    if Pokemon.query.first() is not None:
        logging.info("Database already contains Pokemon data, skipping initialization.")
    else:
        # Load JSON data
        from db import get
        pokemon_data = get()

        # Populate database with Pokemon
        for pokemon in pokemon_data:
            p = Pokemon(**pokemon)
            db.session.add(p)

        db.session.commit()
        logging.info("Pokemon data initialized successfully.")

    # Create a default user if none exists
    if User.query.first() is None:
        default_user = User(user_name="admin")
        db.session.add(default_user)
        db.session.commit()
        logging.info("Default user created successfully.")


def get_all_pokemon(page, per_page, sort_order='asc'):
    """
    Get all Pokemon from the database

    Args:
        page (int): Page number
        per_page (int): Items per page
        sort_order (str): Sort order ('asc' or 'desc')
    """
    # Import here to avoid circular imports
    from .models.Pokemon import Pokemon

    # Apply sorting by Pokemon number
    query = Pokemon.query.order_by(get_sort(sort_order))

    page = PaginatedResponse.create(
        page=page,
        per_page=per_page,
        query=query,
        schema=lambda x: x.to_dict()
    )
    wait()
    return page


def get_pokemon_by_name(name, page, per_page, sort_order='asc'):
    """
    Get Pokemon by name (fuzzy search)

    Args:
        name (str): Name or partial name to search for
        page (int): Page number
        per_page (int): Items per page
        sort_order (str): Sort order ('asc' or 'desc')
    """
    # Import here to avoid circular imports
    from .models.Pokemon import Pokemon
    search_pattern = f"%{name}%"

    # Create a base query with name filter
    query = Pokemon.query.filter(Pokemon.name.ilike(search_pattern)).order_by(get_sort(sort_order))

    page = PaginatedResponse.create(
        query=query,
        schema=lambda x: x.to_dict(),
        page=page,
        per_page=per_page
    )
    wait()
    return page


def get_pokemon_by_type(type_name, page, per_page, sort_order='asc'):
    """
    Get all Pokemon of a specific type

    Args:
        type_name (str): Type to filter by
        page (int): Page number
        per_page (int): Items per page
        sort_order (str): Sort order ('asc' or 'desc')
    """
    # Import here to avoid circular imports
    from .models.Pokemon import Pokemon

    # Create a base query with type filter
    query = Pokemon.query.filter(
        (Pokemon.type_one == type_name) | (Pokemon.type_two == type_name)
    ).order_by(get_sort(sort_order))

    page = PaginatedResponse.create(
        page=page,
        per_page=per_page,
        query=query,
        schema=lambda x: x.to_dict()
    )
    wait()
    return page


def get_all_pokemon_types():
    """
    Get all unique Pokemon types from both type_one and type_two fields

    Returns:
        list: A sorted list of all unique Pokemon types
    """
    # Import here to avoid circular imports
    from .models.Pokemon import Pokemon

    # Create a single query that combines type_one and type_two values using union
    type_one_query = db.session.query(Pokemon.type_one.label('type')).distinct()
    type_two_query = db.session.query(Pokemon.type_two.label('type')).distinct()

    # Use the union method on the query object
    combined_query = type_one_query.union(type_two_query)
    all_types = combined_query.all()

    # Extract values, remove empty strings, and sort
    unique_types = sorted({t[0] for t in all_types if t[0]})
    wait()
    return unique_types


def get_all_users(page, per_page):
    """
    Get all users from the database

    Args:
        page (int): Page number
        per_page (int): Items per page
    """
    # Import here to avoid circular imports
    from .models.User import User

    # Apply sorting by creation date (newest first)
    query = User.query.order_by(User.created_at.desc())

    page = PaginatedResponse.create(
        page=page,
        per_page=per_page,
        query=query,
        schema=lambda x: x.to_dict()
    )
    wait()
    return page


def get_user_by_id(user_id):
    """
    Get a user by ID

    Args:
        user_id (str): The UUID of the user to retrieve
    """
    # Import here to avoid circular imports
    from .models.User import User

    user = User.query.get(user_id)
    wait()
    return user.to_dict() if user else None


def create_user(user_name):
    """
    Create a new user

    Args:
        user_name (str): The username for the new user

    Returns:
        dict: The created user as a dictionary
    """
    # Import here to avoid circular imports
    from .models.User import User

    user = User(user_name=user_name)
    db.session.add(user)
    db.session.commit()
    wait()
    return user.to_dict()
