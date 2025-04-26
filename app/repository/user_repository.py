from app.repository.base_repository import db, wait
from app.utils.PaginatedResponse import PaginatedResponse


def get_all_users(page, per_page):
    """
    Get all users from the database

    Args:
        page (int): Page number
        per_page (int): Items per page
    """
    # Import here to avoid circular imports
    from app.models.User import User

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
    from app.models.User import User

    user = db.session.get(User, user_id)
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
    from app.models.User import User

    user = User(user_name=user_name)
    db.session.add(user)
    db.session.commit()
    return user.to_dict()