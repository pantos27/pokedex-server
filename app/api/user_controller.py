from flask import Blueprint, jsonify, request

from app.repository.user_repository import get_user_by_id, create_user

user_api = Blueprint('user_api', __name__, url_prefix='/api/users')


@user_api.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get a user by ID"""
    user = get_user_by_id(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@user_api.route('', methods=['POST'])
def create_new_user():
    """Create a new user"""
    data = request.get_json()

    if not data or 'user_name' not in data:
        return jsonify({"error": "user_name is required"}), 400

    user_name = data['user_name']

    if not user_name or not isinstance(user_name, str):
        return jsonify({"error": "user_name must be a non-empty string"}), 400

    try:
        user = create_user(user_name)
        return jsonify(user), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
