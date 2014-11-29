
import json

def jsonify(obj):
    return json.dumps(obj, separators=(',', ':'))

