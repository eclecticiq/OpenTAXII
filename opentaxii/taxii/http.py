
from libtaxii.constants import (
    VID_TAXII_XML_11, VID_TAXII_XML_10,
    VID_TAXII_HTTP_10, VID_TAXII_HTTPS_10,
    VID_TAXII_SERVICES_10, VID_TAXII_SERVICES_11
)

from .exceptions import raise_failure

# HTTP Headers
HTTP_CONTENT_TYPE = 'Content-Type'
HTTP_ACCEPT = 'Accept'
HTTP_AUTHORIZATION = 'Authorization'
HTTP_ALLOW = 'Allow'

# TAXII-specific headers
HTTP_X_TAXII_CONTENT_TYPE = 'X-TAXII-Content-Type'
HTTP_X_TAXII_PROTOCOL = 'X-TAXII-Protocol'
HTTP_X_TAXII_ACCEPT = 'X-TAXII-Accept'
HTTP_X_TAXII_SERVICES = 'X-TAXII-Services'

# Custom TAXII header
HTTP_X_TAXII_CONTENT_TYPES = 'X-TAXII-Content-Types'

HTTP_CONTENT_XML = 'application/xml'

BASIC_REQUEST_HEADERS = (HTTP_CONTENT_TYPE, HTTP_X_TAXII_CONTENT_TYPE)

REQUIRED_REQUEST_HEADERS = BASIC_REQUEST_HEADERS + (HTTP_X_TAXII_SERVICES,)
REQUIRED_RESPONSE_HEADERS = (
    HTTP_CONTENT_TYPE, HTTP_X_TAXII_CONTENT_TYPE,
    HTTP_X_TAXII_PROTOCOL, HTTP_X_TAXII_SERVICES)

TAXII_11_HTTPS_Headers = {
    HTTP_CONTENT_TYPE: HTTP_CONTENT_XML,
    HTTP_X_TAXII_CONTENT_TYPE: VID_TAXII_XML_11,
    HTTP_X_TAXII_PROTOCOL: VID_TAXII_HTTPS_10,
    HTTP_X_TAXII_SERVICES: VID_TAXII_SERVICES_11
}

TAXII_11_HTTP_Headers = {
    HTTP_CONTENT_TYPE: HTTP_CONTENT_XML,
    HTTP_X_TAXII_CONTENT_TYPE: VID_TAXII_XML_11,
    HTTP_X_TAXII_PROTOCOL: VID_TAXII_HTTP_10,
    HTTP_X_TAXII_SERVICES: VID_TAXII_SERVICES_11
}

TAXII_10_HTTPS_Headers = {
    HTTP_CONTENT_TYPE: HTTP_CONTENT_XML,
    HTTP_X_TAXII_CONTENT_TYPE: VID_TAXII_XML_10,
    HTTP_X_TAXII_PROTOCOL: VID_TAXII_HTTPS_10,
    HTTP_X_TAXII_SERVICES: VID_TAXII_SERVICES_10
}

TAXII_10_HTTP_Headers = {
    HTTP_CONTENT_TYPE: HTTP_CONTENT_XML,
    HTTP_X_TAXII_CONTENT_TYPE: VID_TAXII_XML_10,
    HTTP_X_TAXII_PROTOCOL: VID_TAXII_HTTP_10,
    HTTP_X_TAXII_SERVICES: VID_TAXII_SERVICES_10
}


def get_content_type(headers):
    return headers[HTTP_X_TAXII_CONTENT_TYPE]


def get_http_headers(version, is_secure):

    taxii_11 = [VID_TAXII_XML_11, VID_TAXII_SERVICES_11]
    taxii_10 = [VID_TAXII_XML_10, VID_TAXII_SERVICES_10]

    if version in taxii_11:
        if is_secure:
            return TAXII_11_HTTPS_Headers
        else:
            return TAXII_11_HTTP_Headers
    elif version in taxii_10:
        if is_secure:
            return TAXII_10_HTTPS_Headers
        else:
            return TAXII_10_HTTP_Headers

    # FIXME: should raise a custom error
    raise ValueError(
        "Unknown combination: version={}, is_secure={}"
        .format(version, is_secure))


def validate_request_headers_post_parse(headers, supported_message_bindings,
                                        service_bindings, protocol_bindings):

    for h in REQUIRED_REQUEST_HEADERS:
        if h not in headers:
            raise_failure("Header %s was not specified" % h)

    taxii_services = headers[HTTP_X_TAXII_SERVICES]

    # These headers are optional
    taxii_protocol = headers.get(HTTP_X_TAXII_PROTOCOL)
    taxii_accept = headers.get(HTTP_X_TAXII_ACCEPT)

    # Validate the X-TAXII-Services header
    if taxii_services not in service_bindings:
        raise_failure(
            "The value of {} was not recognized".format(HTTP_X_TAXII_SERVICES))

    # Validate the X-TAXII-Protocol header
    # FIXME: Look into the service properties
    # instead of assuming both are supported
    if taxii_protocol and taxii_protocol not in protocol_bindings:
        raise_failure(
            "The specified value of X-TAXII-Protocol is not supported")

    # Validate the X-TAXII-Accept header
    # FIXME: Accept more "complex" accept headers
    # (e.g., ones that specify# more than one value)
    if taxii_accept and taxii_accept not in supported_message_bindings:
        raise_failure(
            "The specified value of X-TAXII-Accept is not recognized")


def validate_request_headers(headers, supported_message_bindings):
    for h in BASIC_REQUEST_HEADERS:
        if h not in headers:
            raise_failure("Header %s was not specified" % h)

    if headers[HTTP_X_TAXII_CONTENT_TYPE] not in supported_message_bindings:
        raise_failure(
            'TAXII Content Type "{}" is not supported'
            .format(headers[HTTP_X_TAXII_CONTENT_TYPE]))

    if 'application/xml' not in headers[HTTP_CONTENT_TYPE]:
        raise_failure("The specified value of Content-Type is not supported")


def validate_response_headers(headers):
    for h in REQUIRED_RESPONSE_HEADERS:
        if h not in headers:
            raise ValueError(
                "Required response header not specified: {}".format(h))
