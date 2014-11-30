
import sys
import json
import uuid
import StringIO

from calendar import timegm
from stix.core import STIXPackage


import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


from redis import Redis
redis = Redis()

from settings import INBOX_QUEUE

OUTPUT_QUEUE = 'queue:parsed'


def jsonify(obj):
    return json.dumps(obj, separators=(',', ':'))


def parse_xml(fileobj):
    stix_package = STIXPackage.from_xml(fileobj)
    stix_dict = stix_package.to_dict()
    return stix_package, stix_dict


def compose_xml(stix_dict):
    return STIXPackage.from_dict(stix_dict).to_xml()


def make_iwie(object):

    iwie = dict(
        id = str(uuid.uuid4()),
        meta = dict(
            stix_id = getattr(object, 'id_', None),
            idref = getattr(object, 'idref', None),
            version = getattr(object, 'version', None),
            type = object.__class__.__name__,
        ),
        children = [],
        blob = None
    )

    if getattr(object, 'timestamp', None):
        iwie['meta']['timestamp'] = timegm(object.timestamp.timetuple())

    if hasattr(object, 'operator'):
        iwie['meta']['composition'] = object.operator

    if getattr(object, 'indicators', []):
        iwie['children'].append(map(make_iwie, object.indicators))

    if getattr(object, 'observable_composition', None):
        iwie['children'].append(make_iwie(object.observable_composition))

    if getattr(object, 'observables', []):
        iwie['children'].append(map(make_iwie, object.observables))

    if not iwie['children']:
        iwie['blob'] = object.to_dict()

    return iwie





if __name__ == "__main__":

#    package, blob = parse_xml(sys.stdin)
#    print json.dumps(make_iwie(package))

    while True:
        raw = redis.blpop(INBOX_QUEUE)
        message = json.loads(raw[1])

        log.info("Message received: content_id=%s, collections=%s, binding=%s, len(content)=%s",
                message['content_id'], message['collections'], message['binding'], len(message['content']))

        content = message['content']

        stream = StringIO.StringIO(content)

        try:
            package, blob = parse_xml(stream)
            result = make_iwie(package)
            redis.rpush(OUTPUT_QUEUE, jsonify(result))
            log.info("Message id=%s pushed into %s", message['content_id'], OUTPUT_QUEUE)
        except Exception:
            log.error("Exception while processing content '%s'", message.get('content'), exc_info=True)


