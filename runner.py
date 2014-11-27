import sys

from flask import Flask, request, jsonify, make_response

from taxii.exceptions import StatusMessageException, raise_failure

from taxii.status import process_status_exception
from taxii.services import InboxService, DiscoveryService
from taxii.http import REQUIRED_RESPONSE_HEADERS, get_headers


from functools import wraps


PV_ERR = "There was an error parsing and validating the request message."

app = Flask(__name__)


inbox_service = InboxService('example.com/services/inbox/')
discovery_service = DiscoveryService('example.com/services/discovery/', services=[inbox_service])

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



if __name__ == "__main__":
    app.debug = True

    for service in services:
        app.add_url_rule(
            service.get_path(),
            service.__class__.__name__ + "_view",
            view_func = view_wrapper(service),
            methods = ['POST']
        )

    import flask.ext.color
    flask.ext.color.init_app(app)

    app.run(port=9000)
