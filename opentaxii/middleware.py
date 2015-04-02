import structlog
from functools import wraps
from flask import Flask, request, make_response, abort

from .taxii.exceptions import (
    raise_failure, StatusMessageException, FailureStatus
)
from .taxii.utils import parse_message
from .taxii.status import process_status_exception
from .taxii.bindings import (
    MESSAGE_BINDINGS, SERVICE_BINDINGS, ALL_PROTOCOL_BINDINGS
)
from .taxii.http import (
    get_http_headers, get_content_type, validate_request_headers_post_parse,
    validate_request_headers, validate_response_headers,
    HTTP_X_TAXII_CONTENT_TYPES
)
from .exceptions import UnauthorizedException
from .utils import extract_token
from .management import management
from .local import release_context, context

log = structlog.get_logger(__name__)


def create_app(server):
    '''Create Flask application and attach TAXII server
    instance ``server`` to it.

    :param `opentaxii.server.TAXIIServer` server: TAXII server instance

    :return: Flask app
    '''

    app = Flask(__name__)

    app.taxii = server

    app.add_url_rule("/<path:relative_path>", "opentaxii_services_view",
            _server_wrapper(server), methods=['POST', 'OPTIONS'])

    app.register_blueprint(management, url_prefix='/management')

    app.register_error_handler(500, handle_internal_error)
    app.register_error_handler(StatusMessageException, handle_status_exception)

    return app


def _server_wrapper(server):

    @wraps(_process_with_service)
    def wrapper(relative_path=""):

        relative_path = '/' + relative_path

        token = extract_token(request.headers)

        try:
            if token:
                context.auth_token = token
                context.account = server.auth.get_account(token)

            for service in server.get_services():
                if service.path == relative_path:

                    if not service.available:
                        raise_failure("The service is not available")

                    if service.authentication_required:
                        if not getattr(context, 'account', None):
                            raise UnauthorizedException()

                    if request.method == 'POST':
                        return _process_with_service(service)
                    elif request.method == 'OPTIONS':
                        return _process_options_request(service)
        finally:
            release_context()

        abort(404)

    return wrapper


def _process_with_service(service):

    if 'application/xml' not in request.accept_mimetypes:
        raise_failure("The specified values of Accept is not supported: %s" %
                ", ".join((request.accept_mimetypes or [])))

    validate_request_headers(request.headers, MESSAGE_BINDINGS)

    taxii_message = parse_message(get_content_type(request.headers), request.data)

    try:
        validate_request_headers_post_parse(request.headers,
                supported_message_bindings=MESSAGE_BINDINGS,
                service_bindings=SERVICE_BINDINGS,
                protocol_bindings=ALL_PROTOCOL_BINDINGS)
    except StatusMessageException, e:
        e.in_response_to = taxii_message.message_id
        raise e

    response_message = service.process(request.headers, taxii_message)

    response_headers = get_http_headers(response_message.version, request.is_secure)
    validate_response_headers(response_headers)

    # FIXME: pretty-printing should be configurable
    taxii_xml = response_message.to_xml(pretty_print=True)

    return make_taxii_response(taxii_xml, response_headers)


def _process_options_request(service):

    message_bindings = ','.join(service.supported_message_bindings or [])

    return "", 200, {
        'Allow' : 'POST, OPTIONS',
        HTTP_X_TAXII_CONTENT_TYPES : message_bindings
    }


def make_taxii_response(taxii_xml, taxii_headers):

    validate_response_headers(taxii_headers)
    response = make_response(taxii_xml)

    h = response.headers
    for header, value in taxii_headers.items():
        h[header] = value

    return response


def handle_status_exception(error):
    log.warning('Status exception', exc_info=True)

    if 'application/xml' not in request.accept_mimetypes:
        return 'Unacceptable', 406

    xml, headers = process_status_exception(error, request.headers, request.is_secure)
    return make_taxii_response(xml, headers)


def handle_internal_error(error):
    log.error('Internal error', exc_info=True)

    if 'application/xml' not in request.accept_mimetypes:
        return 'Unacceptable', 406

    new_error = FailureStatus("Error occured", e=error)

    xml, headers = process_status_exception(new_error, request.headers, request.is_secure)
    return make_taxii_response(xml, headers)

