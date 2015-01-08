import sys
from functools import wraps
from flask import Flask, request, jsonify, make_response

from taxii.exceptions import StatusMessageException, raise_failure, StatusFailureMessage

from taxii.status import process_status_exception
from taxii.services import InboxService, DiscoveryService
from taxii.http import REQUIRED_RESPONSE_HEADERS, get_headers

from settings import *

import logging
logging.basicConfig()

app = Flask(__name__)

inbox_service = InboxService(DOMAIN_NAME + '/services/inbox/')
discovery_service = DiscoveryService(DOMAIN_NAME + '/services/discovery/', services=[inbox_service])

services = [inbox_service, discovery_service]


def view_wrapper(service):

    @wraps(service.view)
    def wrapper(*args, **kwargs):

        if 'application/xml' not in request.accept_mimetypes:
            raise_failure("The specified value of Accept is not supported")

        response_message = service.view(request.headers, request.data)
        response_headers = get_headers(response_message, request.is_secure)

        return make_taxii_response(response_message.to_xml(pretty_print=True), response_headers)

    return wrapper


def make_taxii_response(taxii_xml, taxii_headers):

    for h in REQUIRED_RESPONSE_HEADERS:
        if h not in taxii_headers:
            raise ValueError("Required response header not specified: %s" % h)

    r = make_response(taxii_xml)
    for k, v in taxii_headers.items():
        r.headers[k] = v
    return r


@app.errorhandler(StatusMessageException)
def handle_status_exception(error):
    app.logger.error(error.message, exc_info=True)

    if 'application/xml' not in request.accept_mimetypes:
        return 'Unacceptable', 406

    xml, headers = process_status_exception(error, request.headers, request.is_secure)
    return make_taxii_response(xml, headers)


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(error.message, exc_info=True)

    if 'application/xml' not in request.accept_mimetypes:
        return 'Unacceptable', 406

    new_error = StatusFailureMessage("Error occured", e=error)

    xml, headers = process_status_exception(new_error, request.headers, request.is_secure)
    return make_taxii_response(xml, headers)



for service in services:
    app.add_url_rule(
        service.get_path(),
        service.__class__.__name__ + "_view",
        view_func = view_wrapper(service),
        methods = ['POST']
    )


@app.route('/')
def index():
    return "Hey, I'm a TAXII server!"

if __name__ == "__main__":

    if DEBUG:
        app.debug = True

    app.run(port=9000)



