import json
import pytest


def test_get_all_types(client):
    """Test the endpoint to get all Pokemon types."""
    response = client.get('/api/pokemon/types')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_pokemon_by_type(client):
    """Test the endpoint to get Pokemon by type."""
    # Test with a valid type
    response = client.get('/api/pokemon/type/grass')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert 'items' in data

    # If we have results, verify they have the correct type
    if data['items']:
        for pokemon in data['items']:
            assert pokemon['type_one'].lower() == 'grass' or pokemon['type_two'].lower() == 'grass'


def test_search_pokemon_by_name(client):
    """Test the endpoint to search Pokemon by name."""
    response = client.get('/api/pokemon/search?name=bulbasaur')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert isinstance(data, list)

    # If we have results, verify they match the search term
    if data and len(data) > 0 and 'items' in data[0]:
        for pokemon in data[0]['items']:
            assert 'bulbasaur' in pokemon['name'].lower()


def test_search_pokemon_by_type(client):
    """Test the endpoint to search Pokemon by type."""
    response = client.get('/api/pokemon/search?type=grass')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert isinstance(data, dict)

    # If we have results, verify they have the correct type
    if 'items' in data and data['items']:
        for pokemon in data['items']:
            assert pokemon['type_one'].lower() == 'grass' or pokemon['type_two'].lower() == 'grass'


def test_search_pokemon_pagination(client):
    """Test the pagination of Pokemon search results."""
    response = client.get('/api/pokemon/search?page=2&per_page=5')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert 'items' in data
    assert 'meta' in data
    assert data['meta']['page'] == 2
    assert data['meta']['per_page'] == 5


def test_search_pokemon_sort_order(client):
    """Test the sort order of Pokemon search results."""
    response_asc = client.get('/api/pokemon/search?sort_order=asc')
    response_desc = client.get('/api/pokemon/search?sort_order=desc')

    assert response_asc.status_code == 200
    assert response_desc.status_code == 200

    data_asc = json.loads(response_asc.data)
    data_desc = json.loads(response_desc.data)

    # If we have results, verify sort order works
    if ('items' in data_asc and data_asc['items'] and 
        'items' in data_desc and data_desc['items']):
        assert data_asc['items'][0]['id'] != data_desc['items'][0]['id']


def test_get_icon_url(client):
    """Test the endpoint to get a Pokemon icon URL."""
    response = client.get('/api/pokemon/icon/bulbasaur')
    assert response.status_code == 200

    # The response should be a URL string
    assert b"https://img.pokemondb.net/sprites/silver/normal/bulbasaur.png" in response.data


def test_user_api(client):
    """Test the user API endpoints."""
    # First, create a user
    response = client.post('/api/users', json={'user_name': 'testuser'})
    assert response.status_code == 201

    data = json.loads(response.data)
    assert 'id' in data
    assert data['user_name'] == 'testuser'

    user_id = data['id']

    # Then, get the user by ID
    response = client.get(f'/api/users/{user_id}')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['id'] == user_id
    assert data['user_name'] == 'testuser'


def test_capture_api(client):
    """Test the capture API endpoints."""
    # First, create a user
    response = client.post('/api/users', json={'user_name': 'captureuser'})
    assert response.status_code == 201

    data = json.loads(response.data)
    user_id = data['id']

    # Then, create a capture
    pokemon_id = 1  # Assuming Pokemon with ID 1 exists
    response = client.post(f'/api/captures', json={
        'user_id': user_id,
        'pokemon_id': pokemon_id
    })
    assert response.status_code == 201

    data = json.loads(response.data)
    assert data['user_id'] == user_id
    assert data['pokemon_id'] == pokemon_id

    # Verify the user has the captured Pokemon
    response = client.get(f'/api/users/{user_id}')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert pokemon_id in data['captured_pokemon']
