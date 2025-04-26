from app.repository.base_repository import db, wait


def create_capture(user_id, pokemon_id):
    """
    Create a new capture record

    Args:
        user_id (str): The UUID of the user who captured the Pokemon
        pokemon_id (int): The ID of the captured Pokemon

    Returns:
        dict: The created capture record as a dictionary
    """
    # Import here to avoid circular imports
    from app.models.Captured import Captured
    from app.models.User import User
    from app.models.Pokemon import Pokemon

    # Verify that the user and pokemon exist
    user = db.session.get(User, user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} not found")

    pokemon = db.session.get(Pokemon, pokemon_id)
    if not pokemon:
        raise ValueError(f"Pokemon with ID {pokemon_id} not found")

    capture = Captured(user_id=user_id, pokemon_id=pokemon_id)
    db.session.add(capture)
    db.session.commit()
    wait()
    return capture.to_dict()