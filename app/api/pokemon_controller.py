from flask import Blueprint, jsonify, request

from app.repository.pokemon_repository import get_pokemon, get_all_pokemon_types

api = Blueprint('api', __name__, url_prefix='/api/pokemon')


@api.route('/icon/<name>')
def get_icon_url(name: str):
    """Get the icon URL for a Pokémon"""
    return f"https://img.pokemondb.net/sprites/silver/normal/{name.lower()}.png"


@api.route('/type/<type_name>')
def get_pokemon_by_type_route(type_name: str):
    """Get all Pokémon of a specific type"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)

    pokemon_list = get_pokemon(type_name=type_name, page=page, per_page=per_page)
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

    per_page = min(per_page, 100)

    pokemon_list = get_pokemon(
        name=name, 
        type_name=poke_type, 
        page=page, 
        per_page=per_page, 
        sort_order=sort_order
    )

    return jsonify(pokemon_list)


@api.route('/types')
def get_all_types():
    """Get all unique Pokemon types"""
    types = get_all_pokemon_types()
    return jsonify(types)
