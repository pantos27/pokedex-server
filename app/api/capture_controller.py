from flask import Blueprint, jsonify, request

from app.repository.captured_repository import create_capture

# Create a blueprint for the capture API routes
capture_api = Blueprint('capture_api', __name__, url_prefix='/api/captures')


@capture_api.route('', methods=['POST'])
def create_new_capture():
    """Create a new capture record"""
    data = request.get_json()
    user_id = request.headers.get('X-User-ID')

    # Validate request data
    if not data or 'pokemon_id' not in data or not user_id:
        return jsonify({"error": "Request must include user_id and pokemon_id"}), 400

    pokemon_id = data['pokemon_id']

    # Convert pokemon_id to integer if needed
    if not isinstance(pokemon_id, int):
        try:
            pokemon_id = int(pokemon_id)
        except (ValueError, TypeError):
            return jsonify({"error": "pokemon_id must be a valid integer"}), 400

    try:
        capture = create_capture(user_id, pokemon_id)
        return jsonify(capture), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400
