from flask import Blueprint, jsonify

health = Blueprint('health', __name__)

@health.route('', methods=['GET'])
def index():
    return jsonify(alive=True)

