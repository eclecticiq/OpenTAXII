from libtaxii.constants import *
import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.common import generate_message_id

from copy import deepcopy

from .http import *


def process_status_exception(exception, headers, is_secure):

    accepted_content = headers.get(HTTP_X_TAXII_ACCEPT)

    if not accepted_content:  # Can respond with whatever we want. try to use the X-TAXII-Content-Type header to pick
        accepted_content = headers.get(HTTP_X_TAXII_CONTENT_TYPE)

    if accepted_content == VID_TAXII_XML_10:
        sm = exception_to_status(exception, 10)
        version = VID_TAXII_SERVICES_10
    elif accepted_content == VID_TAXII_XML_11:
        sm = exception_to_status(exception, 11)
        version = VID_TAXII_SERVICES_11
    else:
        #FIXME: Unknown accepted content. Pretending X-TAXII-Accept was TAXII 1.1
        sm = exception_to_status(exception, 11)
        version = VID_TAXII_SERVICES_11

    response_headers = get_http_headers(version, is_secure)

    return (sm.to_xml(pretty_print=True), response_headers)


def exception_to_status_format(exception, format):
    if format == VID_TAXII_XML_11:
        return exception_to_status(exception, 11)
    elif format == VID_TAXII_XML_10:
        return exception_to_status(exception, 10)
    else:
        raise ValueError("Unknown value for format: %s" % format)


def exception_to_status(exception, version):

    data = dict(
        message_id = generate_message_id(),
        in_response_to = exception.in_response_to,
        extended_headers = exception.extended_headers,
        status_type = exception.status_type,
        status_detail = exception.status_detail,
        message = exception.message
    )

    if version == 11:
        sm = tm11.StatusMessage(**data)
    elif version == 10:
        sm = tm10.StatusMessage(**data)

    return sm


