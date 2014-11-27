
from libtaxii.constants import *

from .bindings import *
from .exceptions import raise_failure
from .transform import parse_message

from copy import deepcopy

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


def verify_headers_pre_parse(headers):

    for h in BASIC_REQUEST_HEADERS:
        if not h in headers:
            raise_failure("Header %s was not specified" % h)

    if headers[HTTP_X_TAXII_CONTENT_TYPE] not in MESSAGE_BINDINGS:
        raise_failure('TAXII Content Type "%s" is not supported' % headers[HTTP_X_TAXII_CONTENT_TYPE])

    if 'application/xml' not in headers[HTTP_CONTENT_TYPE]:
        raise_failure("The specified value of Content-Type is not supported")

    return True


def verify_headers_post_parse(headers, in_response_to=None):

    for h in REQUIRED_REQUEST_HEADERS:
        if not h in headers:
            raise_failure("Header %s was not specified" % h, in_response_to=in_response_to)

    taxii_services = headers[HTTP_X_TAXII_SERVICES]

    # These headers are optional
    taxii_protocol = headers.get(HTTP_X_TAXII_PROTOCOL)
    taxii_accept = headers.get(HTTP_X_TAXII_ACCEPT)

    # Validate the X-TAXII-Services header
    if taxii_services not in SERVICE_BINDINGS:
        raise_failure("The value of %s was not recognized" % HTTP_X_TAXII_SERVICES, in_response_to=in_response_to)

    # Validate the X-TAXII-Protocol header
    # TODO: Look into the service properties instead of assuming both are supported
    # ?
    if taxii_protocol and taxii_protocol not in ALL_PROTOCOL_BINDINGS:
        raise_failure("The specified value of X-TAXII-Protocol is not supported", in_response_to=in_response_to)

    # Validate the X-TAXII-Accept header
    # TODO: Accept more "complex" accept headers (e.g., ones that specify more than one value)
    if taxii_accept and taxii_accept not in MESSAGE_BINDINGS:
        raise_failure("The specified value of X-TAXII-Accept is not recognized", in_response_to=in_response_to)


def verify_headers_and_parse(headers, body):
    verify_headers_pre_parse(headers)
    taxii_message = parse_message(headers[HTTP_X_TAXII_CONTENT_TYPE], body)
    verify_headers_post_parse(headers, in_response_to=taxii_message.message_id)
    return taxii_message


def get_headers(taxii_message, is_secure):

    version = VID_TAXII_SERVICES_11 #FIXME: waiting for merge https://github.com/TAXIIProject/libtaxii/issues/149
    #taxii_message.version

    if is_secure:
        if version == VID_TAXII_SERVICES_11:
            return deepcopy(TAXII_11_HTTPS_Headers)
        elif version == VID_TAXII_SERVICES_10:
            return deepcopy(TAXII_10_HTTPS_Headers)

    else:
        if version == VID_TAXII_SERVICES_11:
            return deepcopy(TAXII_11_HTTP_Headers)
        elif version == VID_TAXII_SERVICES_10:
            return deepcopy(TAXII_10_HTTP_Headers)

    raise ValueError("Unknown combination for services_version and is_secure")
