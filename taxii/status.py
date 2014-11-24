from libtaxii.constants import *
import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.common import generate_message_id

from copy import deepcopy

from .http import *

def get_headers(taxii_services_version, is_secure):
    """
    Convenience method for selecting headers
    """
    if taxii_services_version == VID_TAXII_SERVICES_11:
        if is_secure:
            return deepcopy(TAXII_11_HTTPS_Headers)
        else:
            return deepcopy(TAXII_11_HTTP_Headers)
    elif taxii_services_version == VID_TAXII_SERVICES_10:
        if is_secure:
            return deepcopy(TAXII_10_HTTPS_Headers)
        else:
            return deepcopy(TAXII_10_HTTP_Headers)
    else:
        raise ValueError("Unknown combination for taxii_services_version and is_secure!")


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
        #FIXME: For now, just pretend X-TAXII-Accept was TAXII 1.1
        # Not 100% sure what the right response is... HTTP Unacceptable?
        # Squash the exception argument and create a new one for unknown HTTP Accept?
        sm = exception_to_status(exception, 11)
        version = VID_TAXII_SERVICES_11

    response_headers = get_headers(version, is_secure)

    return (sm.to_xml(pretty_print=True), response_headers)


def exception_to_status_format(exception, format):
    if format == VID_TAXII_XML_11:
        return exception_to_status(exception, 11)
    elif format == VID_TAXII_XML_10:
        return exception_to_status(exception, 10)
    else:
        raise ValueError("Unknown value for format: %s" % format)


def exception_to_status(exception, v):

    data = dict(
        message_id = generate_message_id(),
        in_response_to = exception.in_response_to,
        extended_headers = exception.extended_headers,
        status_type = exception.status_type,
        status_detail = exception.status_detail,
        message = exception.message
    )

    if v == 11:
        sm = tm11.StatusMessage(**data)
    elif v == 10:
        sm = tm10.StatusMessage(**data)

    return sm


