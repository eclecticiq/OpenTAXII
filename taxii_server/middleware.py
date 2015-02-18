import importlib
from functools import wraps
from flask import Flask, request, jsonify, make_response

from .taxii.exceptions import raise_failure
from .taxii.http import *
from .taxii.transform import parse_message
from .taxii.exceptions import StatusMessageException, StatusFailureMessage
from .taxii.status import process_status_exception

from .options import ServerConfig
from .server import TAXIIServer
from .data.sql import SQLDB
from .data import DataManager
from .utils import configure_logging

import structlog
log = structlog.get_logger(__name__)


def create_app(server_properties=None, services_properties=None):

    config = ServerConfig(server_properties=server_properties,
            services_properties=services_properties)

    app = Flask(__name__)
    app = attach_taxii_server(app, create_server(config))

    app.taxii_config = config

    app.register_error_handler(500, handle_internal_error)
    app.register_error_handler(StatusMessageException, handle_status_exception)

    return app


def create_server(config):

    manager = DataManager(
        config = config,
        api = SQLDB(**config['server']['api'])
    )

    server = TAXIIServer(
        domain = config['server']['domain'],
        data_manager = manager
    )

    if config['server']['hooks']:
        importlib.import_module(config['server']['hooks'])

    return server


def attach_taxii_server(app, server):

    for path, service in server.path_to_service.items():
        app.add_url_rule(
            path,
            service.uid + "_view",
            view_func = service_wrapper(service),
            methods = ['POST']
        )

    return app


def service_wrapper(service):

    @wraps(service.process)
    def wrapper(*args, **kwargs):

        if 'application/xml' not in request.accept_mimetypes:
            raise_failure("The specified values of Accept is not supported: %s" % (request.accept_mimetypes or []))

        validate_request_headers(request.headers)

        body = request.data

        taxii_message = parse_message(get_content_type(request.headers), body)
        try:
            validate_request_headers_post_parse(request.headers)
        except StatusMessageException, e:
            e.in_response_to = taxii_message.message_id
            raise e

        response_message = service.process(request.headers, taxii_message)

        response_headers = get_http_headers(response_message.version, request.is_secure)
        validate_response_headers(response_headers)

        #FIXME: pretty-printing should be configurable
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




