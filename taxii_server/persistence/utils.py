
import json
from datetime import datetime
import calendar

def jsonify(obj):
    return json.dumps(obj, separators=(',', ':'))


def date_to_ts(obj):
    if not isinstance(obj, datetime):
        raise ValueError('Datetime object expected: %s' % obj)

    if obj.utcoffset() is not None:
        obj = obj - obj.utcoffset()

    millis = int(
        calendar.timegm(obj.timetuple()) * 1000 +
        obj.microsecond / 1000
    )
    return millis
