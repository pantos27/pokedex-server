from sqlalchemy import or_

from app.repository.base_repository import db, wait
from app.utils.PaginatedResponse import PaginatedResponse


def get_sort(sort_order):
    from app.models.Pokemon import Pokemon
    return (
        Pokemon.number.asc() if sort_order.lower() == 'asc' else Pokemon.number.desc()
    )


def get_all_pokemon(page, per_page, sort_order='asc'):
    """
    Get all Pokémon from the database

    Args:
        page (int): Page number
        per_page (int): Items per page
        sort_order (str): Sort order ('asc' or 'desc')
    """
    # Import here to avoid circular imports
    from app.models.Pokemon import Pokemon

    # Apply sorting by Pokémon number
    query = Pokemon.query.order_by(get_sort(sort_order))

    page = PaginatedResponse.create(
        page=page,
        per_page=per_page,
        query=query,
        schema=lambda x: x.to_dict()
    )
    wait()
    return page


def get_pokemon(name=None, type_name=None, page=1, per_page=10, sort_order='asc'):
    """
    Get Pokémon with optional filtering by name and/or type

    Args:
        name (str, optional): Text to search for across Pokemon name and type fields
        type_name (str, optional): Type to filter by
        page (int): Page number
        per_page (int): Items per page
        sort_order (str): Sort order ('asc' or 'desc')
    """
    # Import here to avoid circular imports
    from app.models.Pokemon import Pokemon

    # Start with a base query
    query = Pokemon.query

    # Apply name filter if provided
    if name:
        search_pattern = f"%{name}%"
        query = query.filter(
            or_(
                # String fields for name search
                Pokemon.name.ilike(search_pattern),
                Pokemon.type_one.ilike(search_pattern),
                Pokemon.type_two.ilike(search_pattern),
            )
        )

    # Apply type filter if provided
    if type_name:
        query = query.filter(
            (Pokemon.type_one == type_name) | (Pokemon.type_two == type_name)
        )

    # Apply sorting
    query = query.order_by(get_sort(sort_order))

    # Create a paginated response
    page = PaginatedResponse.create(
        query=query,
        schema=lambda x: x.to_dict(),
        page=page,
        per_page=per_page
    )
    wait()
    return page


def get_all_pokemon_types():
    """
    Get all unique Pokémon types from both type_one and type_two fields

    Returns:
        list: A sorted list of all unique Pokémon types
    """
    # Import here to avoid circular imports
    from app.models.Pokemon import Pokemon

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