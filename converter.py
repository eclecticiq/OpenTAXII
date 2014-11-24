
import sys
import json
import uuid

from calendar import timegm

from stix.core import STIXPackage

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

    package, blob = parse_xml(sys.stdin)

    print json.dumps(make_iwie(package))

