from libtaxii import messages_10 as tm10
from libtaxii import messages_11 as tm11

from taxii_server.taxii.http import *

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


