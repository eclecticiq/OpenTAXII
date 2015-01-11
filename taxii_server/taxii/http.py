
from libtaxii.constants import *

from .bindings import *
from .exceptions import raise_failure
from .transform import parse_message

#: HTTP Headers
HTTP_CONTENT_TYPE = 'Content-Type'
HTTP_ACCEPT = 'Accept'
HTTP_X_TAXII_CONTENT_TYPE = 'X-TAXII-Content-Type'
HTTP_X_TAXII_PROTOCOL = 'X-TAXII-Protocol'
HTTP_X_TAXII_ACCEPT = 'X-TAXII-Accept'
HTTP_X_TAXII_SERVICES = 'X-TAXII-Services'

BASIC_REQUEST_HEADERS = (HTTP_CONTENT_TYPE, HTTP_X_TAXII_CONTENT_TYPE)

REQUIRED_REQUEST_HEADERS = BASIC_REQUEST_HEADERS + (HTTP_X_TAXII_SERVICES,)
REQUIRED_RESPONSE_HEADERS = (HTTP_CONTENT_TYPE, HTTP_X_TAXII_CONTENT_TYPE, HTTP_X_TAXII_PROTOCOL, HTTP_X_TAXII_SERVICES)

TAXII_11_HTTPS_Headers = {
    HTTP_CONTENT_TYPE: 'application/xml',
    HTTP_X_TAXII_CONTENT_TYPE: VID_TAXII_XML_11,
    HTTP_X_TAXII_PROTOCOL: VID_TAXII_HTTPS_10,
    HTTP_X_TAXII_SERVICES: VID_TAXII_SERVICES_11
}

TAXII_11_HTTP_Headers = {
    HTTP_CONTENT_TYPE: 'application/xml',
    HTTP_X_TAXII_CONTENT_TYPE: VID_TAXII_XML_11,
    HTTP_X_TAXII_PROTOCOL: VID_TAXII_HTTP_10,
    HTTP_X_TAXII_SERVICES: VID_TAXII_SERVICES_11
}

TAXII_10_HTTPS_Headers = {
    HTTP_CONTENT_TYPE: 'application/xml',
    HTTP_X_TAXII_CONTENT_TYPE: VID_TAXII_XML_10,
    HTTP_X_TAXII_PROTOCOL: VID_TAXII_HTTPS_10,
    HTTP_X_TAXII_SERVICES: VID_TAXII_SERVICES_10
}

TAXII_10_HTTP_Headers = {
    HTTP_CONTENT_TYPE: 'application/xml',
    HTTP_X_TAXII_CONTENT_TYPE: VID_TAXII_XML_10,
    HTTP_X_TAXII_PROTOCOL: VID_TAXII_HTTP_10,
    HTTP_X_TAXII_SERVICES: VID_TAXII_SERVICES_10
}


def get_content_type(headers):
    return headers[HTTP_X_TAXII_CONTENT_TYPE]


def get_http_headers(taxii_message, is_secure):

    version = taxii_message.version

    if is_secure:
        if version == VID_TAXII_XML_11:
            return TAXII_11_HTTPS_Headers
        elif version == VID_TAXII_XML_10:
            return TAXII_10_HTTPS_Headers

    else:
        if version == VID_TAXII_XML_11:
            return TAXII_11_HTTP_Headers
        elif version == VID_TAXII_XML_10:
            return TAXII_10_HTTP_Headers

    raise ValueError("Unknown combination for services_version and is_secure")



