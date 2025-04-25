from flask import Blueprint, jsonify, request

from app.repository import get_all_pokemon, get_pokemon_by_name, get_pokemon_by_type

# Create a blueprint for the API routes
api = Blueprint('api', __name__)


@api.route('/icon/<name>')
def get_icon_url(name: str):
    """Get the icon URL for a Pokemon"""
    return f"https://img.pokemondb.net/sprites/silver/normal/{name.lower()}.png"


@api.route('/type/<type_name>')
def get_pokemon_by_type_route(type_name: str):
    """Get all Pokemon of a specific type"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)

    pokemon_list = get_pokemon_by_type(type_name,page,per_page)
    return jsonify(pokemon_list)


@api.route('/search')
def search_pokemon():
    """Search Pokemon by various criteria"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort_order = request.args.get('sort_order', 'asc', type=str).lower()
    assert sort_order in ('asc', 'desc'), (
        f"Invalid sort order: {sort_order}. "
        "Valid values are 'asc' or 'desc'."
    )
    name = request.args.get('name')
    poke_type = request.args.get('type')

    # Cap per_page to avoid performance issues
    per_page = min(per_page, 100)

    # Example implementation - you could expand this based on your needs
    if name is not None:
        pokemon = get_pokemon_by_name(name,page,per_page,sort_order)
        return jsonify([pokemon] if pokemon else [])

    if poke_type is not None:
        pokemon_list = get_pokemon_by_type(poke_type,page,per_page,sort_order)
        return jsonify(pokemon_list)

    # Default to returning all Pokemon
    return jsonify(get_all_pokemon(page,per_page,sort_order))
