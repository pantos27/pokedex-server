from flask import Blueprint, jsonify, request

from app.db import get_all_pokemon, get_pokemon_by_name, get_pokemon_by_type

# Create a blueprint for the API routes
api = Blueprint('api', __name__)


@api.route('/icon/<name>')
def get_icon_url(name: str):
    """Get the icon URL for a Pokemon"""
    return f"https://img.pokemondb.net/sprites/silver/normal/{name}.png"


@api.route('/')
def get_all_pokemon_route():
    """Get all Pokemon"""
    data = get_all_pokemon()
    return jsonify(data)


@api.route('/pokemon/<name>')
def get_pokemon_by_name_route(name: str):
    """Get a specific Pokémon by name"""
    pokemon = get_pokemon_by_name(name)
    if not pokemon:
        return jsonify({"error": "Pokemon not found"}), 404
    return jsonify(pokemon)


@api.route('/type/<type_name>')
def get_pokemon_by_type_route(type_name: str):
    """Get all Pokemon of a specific type"""
    pokemon_list = get_pokemon_by_type(type_name)
    return jsonify(pokemon_list)


@api.route('/search')
def search_pokemon():
    """Search Pokemon by various criteria"""
    query_params = request.args

    # Example implementation - you could expand this based on your needs
    if 'name' in query_params:
        pokemon = get_pokemon_by_name(query_params['name'])
        return jsonify([pokemon] if pokemon else [])

    if 'type' in query_params:
        pokemon_list = get_pokemon_by_type(query_params['type'])
        return jsonify(pokemon_list)

    # Default to returning all Pokemon
    return jsonify(get_all_pokemon())
