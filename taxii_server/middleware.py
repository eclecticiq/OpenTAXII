from functools import wraps
from flask import Request, request, make_response

from .taxii.exceptions import raise_failure
from .taxii.http import *
from .taxii.transform import parse_message
from .taxii.exceptions import StatusMessageException
from .taxii.status import process_status_exception

import logging
log = logging.getLogger(__name__)

class TAXIIMiddleware(object):

    def __init__(self, app):
        self.app = app


    def __call__(self, environ, start_response):

        _request = Request(environ)

        if 'application/xml' not in _request.accept_mimetypes:
            raise_failure("The specified values of Accept is not supported: %s" % _request.accept_mimetypes)

        validate_request_headers(_request.headers)

        return self.app(environ, start_response)


def service_wrapper(service):

    @wraps(service.view)
    def wrapper(*args, **kwargs):

        request_headers = request.headers
        body = request.data

        taxii_message = parse_message(get_content_type(request_headers), body)
        try:
            validate_request_headers_post_parse(request_headers)
        except StatusMessageException, e:
            e.in_response_to = taxii_message.message_id
            raise e

        response_message = service.view(request_headers, taxii_message)
        response_headers = get_http_headers(response_message, request.is_secure)

        validate_response_headers(response_headers)

        #FIXME: should be configurable
        taxii_xml = response_message.to_xml(pretty_print=True)

        return make_taxii_response(taxii_xml, response_headers)

    return wrapper



def validate_request_headers(headers):
    for h in BASIC_REQUEST_HEADERS:
        if not h in headers:
            raise_failure("Header %s was not specified" % h)

    if headers[HTTP_X_TAXII_CONTENT_TYPE] not in MESSAGE_BINDINGS:
        raise_failure('TAXII Content Type "%s" is not supported' % headers[HTTP_X_TAXII_CONTENT_TYPE])

    if 'application/xml' not in headers[HTTP_CONTENT_TYPE]:
        raise_failure("The specified value of Content-Type is not supported")


def validate_request_headers_post_parse(headers):
    for h in REQUIRED_REQUEST_HEADERS:
        if not h in headers:
            raise_failure("Header %s was not specified" % h)

    taxii_services = headers[HTTP_X_TAXII_SERVICES]

    # These headers are optional
    taxii_protocol = headers.get(HTTP_X_TAXII_PROTOCOL)
    taxii_accept = headers.get(HTTP_X_TAXII_ACCEPT)

    # Validate the X-TAXII-Services header
    if taxii_services not in SERVICE_BINDINGS:
        raise_failure("The value of %s was not recognized" % HTTP_X_TAXII_SERVICES)

    # Validate the X-TAXII-Protocol header
    # TODO: Look into the service properties instead of assuming both are supported
    # ?
    if taxii_protocol and taxii_protocol not in ALL_PROTOCOL_BINDINGS:
        raise_failure("The specified value of X-TAXII-Protocol is not supported")

    # Validate the X-TAXII-Accept header
    # TODO: Accept more "complex" accept headers (e.g., ones that specify more than one value)
    if taxii_accept and taxii_accept not in MESSAGE_BINDINGS:
        raise_failure("The specified value of X-TAXII-Accept is not recognized")


def validate_response_headers(headers):
    for h in REQUIRED_RESPONSE_HEADERS:
        if h not in headers:
            raise ValueError("Required response header not specified: %s" % h)


def make_taxii_response(taxii_xml, taxii_headers):

    validate_response_headers(taxii_headers)

    response = make_response(taxii_xml)

    h = response.headers
    for header, value in taxii_headers.items():
        h[header] = value

    return response


def handle_status_exception(error):
    log.error('Status exception: %s' % error, exc_info=True)

    if 'application/xml' not in request.accept_mimetypes:
        return 'Unacceptable', 406

    xml, headers = process_status_exception(error, request.headers, request.is_secure)
    return make_taxii_response(xml, headers)


def handle_internal_error(error):
    log.error('Internal error: %s' % error, exc_info=True)

    if 'application/xml' not in request.accept_mimetypes:
        return 'Unacceptable', 406

    new_error = StatusFailureMessage("Error occured", e=error)

    xml, headers = process_status_exception(new_error, request.headers, request.is_secure)
    return make_taxii_response(xml, headers)


def attach_error_handlers(app):

    app.errorhandler(StatusMessageException)(handle_status_exception)
    app.errorhandler(500)(handle_internal_error)


