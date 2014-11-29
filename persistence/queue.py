
from redis import Redis

from .utils import jsonify

redis = Redis()

def push(queue_name, *objects):
    if not objects:
        return
    redis.rpush(queue_name, *map(jsonify, objects))
