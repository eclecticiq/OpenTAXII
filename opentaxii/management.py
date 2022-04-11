from flask import Blueprint, abort, jsonify, request

from .local import context

management = Blueprint('management', __name__)


@management.route('/auth', methods=['POST'])
def auth():
    data = request.get_json(silent=True) or request.form

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return 'Both username and password are required', 400

    token = context.server.auth.authenticate(username, password)

    if not token:
        abort(401)

    return jsonify(token=token)


@management.route('/health', methods=['GET'])
def health():
    return jsonify(alive=True)
