from flask import Blueprint, request, jsonify, abort, current_app

management = Blueprint('some', __name__)

@management.route('/auth', methods=['POST'])
def auth():
    data = request.get_json() or request.form

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return 'Both username and password are required', 400

    token = current_app.taxii.auth.authenticate(username, password)

    if not token:
        abort(401)
    
    return jsonify(token=token)

