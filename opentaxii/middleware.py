import functools

import structlog
from flask import Flask, request
from marshmallow.exceptions import \
    ValidationError as MarshmallowValidationError
from werkzeug.exceptions import HTTPException

from .exceptions import InvalidAuthHeader
from .local import context, release_context
from .management import management
from .taxii.exceptions import StatusMessageException
from .taxii.http import HTTP_AUTHORIZATION
from .utils import parse_basic_auth_token

log = structlog.get_logger(__name__)


def create_app(server):
    """Create Flask application and attach TAXII server
    instance ``server`` to it.

    :param `opentaxii.server.TAXIIServer` server: TAXII server instance

    :return: Flask app
    """

    app = Flask(__name__)
    app.taxii_server = server

    server.init_app(app)

    app.add_url_rule(
        "/<path:relative_path>",
        "opentaxii_services_view",
        server.handle_request,
        methods=["GET", "POST", "OPTIONS", "DELETE"],
    )

    app.register_blueprint(management, url_prefix="/management")

    app.register_error_handler(500, server.handle_internal_error)
    app.register_error_handler(StatusMessageException, server.handle_status_exception)
    app.register_error_handler(HTTPException, server.handle_http_exception)
    app.register_error_handler(MarshmallowValidationError, server.handle_validation_exception)
    app.before_request(functools.partial(create_context_before_request, server))
    app.after_request(cleanup_context)
    return app


def create_context_before_request(server):
    context.account = _authenticate(server, request.headers)
    context.server = server


def cleanup_context(response):
    release_context()
    return response


def _authenticate(server, headers):

    auth_header = headers.get(HTTP_AUTHORIZATION)
    if not auth_header:
        return None

    parts = auth_header.split(" ", 1)

    if len(parts) != 2:
        log.warning("auth.header_invalid", value=auth_header)
        return None

    auth_type, raw_token = parts
    auth_type = auth_type.lower()

    if auth_type == "basic":

        if not server.is_basic_auth_supported():
            server.raise_unauthorized()

        try:
            username, password = parse_basic_auth_token(raw_token)
        except InvalidAuthHeader:
            log.error(
                "auth.basic_auth.header_invalid", raw_token=raw_token, exc_info=True
            )
            return None

        token = server.auth.authenticate(username, password)

    elif auth_type == "bearer":
        token = raw_token
    else:
        server.raise_unauthorized()

    if not token:
        server.raise_unauthorized()

    account = server.auth.get_account(token)

    if not account:
        server.raise_unauthorized()

    return account
