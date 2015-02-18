from libtaxii import messages_10 as tm10
from libtaxii import messages_11 as tm11

from taxii_server.taxii.http import *
from taxii_server.taxii.utils import get_utc_now

from fixtures import *

def as_tm(version):
    if version == 10:
        return tm10
    elif version == 11:
        return tm11
    else:
        raise ValueError('Unknown TAXII message version: %s' % version)


def get_service(server, service_id):
    for service in server.services:
        if service.id == service_id:
            return service


def prepare_headers(version, https):
    headers = dict()
    if version == 10:
        if https:
            headers.update(TAXII_10_HTTPS_Headers)
        else:
            headers.update(TAXII_10_HTTP_Headers)
    elif version == 11:
        if https:
            headers.update(TAXII_11_HTTPS_Headers)
        else:
            headers.update(TAXII_11_HTTP_Headers)
    else:
        raise ValueError('Unknown TAXII message version: %s' % version)

    headers[HTTP_ACCEPT] = HTTP_CONTENT_XML
    return headers


def persist_content(manager, collection_name, service_id, timestamp=None):

    timestamp = timestamp or get_utc_now()

    content = entities.ContentBlockEntity(content=CONTENT, timestamp_label=timestamp,
            message=MESSAGE, content_binding=BINDING_ENTITY)

    collection = manager.get_collection(collection_name, service_id)

    content = manager.save_content(content, collections=[collection])

    return content

