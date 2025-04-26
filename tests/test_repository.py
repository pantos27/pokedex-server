import pytest
from app.repository import (
    get_all_pokemon,
    get_pokemon,
    get_all_pokemon_types,
    get_user_by_id,
    create_user,
    create_capture
)


def test_get_all_pokemon(app):
    """Test retrieving all Pokemon with pagination."""
    with app.app_context():
        # Test default parameters
        result = get_all_pokemon(1, 10)
        assert isinstance(result, dict)
        assert 'items' in result
        assert 'meta' in result
        assert len(result['items']) <= 10

        # Test with different page and per_page
        result = get_all_pokemon(2, 5)
        assert len(result['items']) <= 5

        # Test with different sort order
        result_asc = get_all_pokemon(1, 10, 'asc')
        result_desc = get_all_pokemon(1, 10, 'desc')

        # Verify sort order works (if there are items)
        if result_asc['items'] and result_desc['items']:
            assert result_asc['items'][0]['id'] != result_desc['items'][0]['id']


def test_get_all_pokemon_types(app):
    """Test retrieving all Pokemon types."""
    with app.app_context():
        result = get_all_pokemon_types()
        assert isinstance(result, list)
        # There should be at least some types
        assert len(result) > 0


def test_get_pokemon_unified(app):
    """Test the unified get_pokemon function with different parameter combinations."""
    with app.app_context():
        # Test with no filters (should return all Pokemon)
        result = get_pokemon()
        assert isinstance(result, dict)
        assert 'items' in result
        assert 'meta' in result
        assert len(result['items']) > 0

        # Test with name filter only
        result = get_pokemon(name='bulbasaur')
        assert isinstance(result, dict)
        assert 'items' in result
        if result['items']:
            for pokemon in result['items']:
                assert 'bulbasaur' in pokemon['name'].lower()

        # Test with type filter only
        result = get_pokemon(type_name='grass')
        assert isinstance(result, dict)
        assert 'items' in result
        if result['items']:
            for pokemon in result['items']:
                assert pokemon['type_one'].lower() == 'grass' or pokemon['type_two'].lower() == 'grass'

        # Test with both name and type filters
        result = get_pokemon(name='saur', type_name='grass')
        assert isinstance(result, dict)
        assert 'items' in result
        if result['items']:
            for pokemon in result['items']:
                assert 'saur' in pokemon['name'].lower()
                assert pokemon['type_one'].lower() == 'grass' or pokemon['type_two'].lower() == 'grass'


def test_user_operations(app):
    """Test user creation and retrieval."""
    with app.app_context():
        # Create a user
        username = "testuser"
        user = create_user(username)
        assert user is not None
        assert user['user_name'] == username

        # Retrieve the user
        user_id = user['id']
        retrieved_user = get_user_by_id(user_id)
        assert retrieved_user is not None
        assert retrieved_user['id'] == user_id
        assert retrieved_user['user_name'] == username


def test_capture_operations(app):
    """Test creating a capture."""
    with app.app_context():
        # Create a user
        user = create_user("captureuser")
        user_id = user['id']

        # Create a capture (assuming Pokemon with ID 1 exists)
        pokemon_id = 1
        capture = create_capture(user_id, pokemon_id)
        assert capture is not None
        assert capture['user_id'] == user_id
        assert capture['pokemon_id'] == pokemon_id

        # Verify the user has the captured Pokemon
        user = get_user_by_id(user_id)
        assert pokemon_id in user['captured_pokemon']
