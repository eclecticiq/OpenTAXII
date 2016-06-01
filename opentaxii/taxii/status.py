import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.common import generate_message_id

from libtaxii.constants import (
    VID_TAXII_XML_11, VID_TAXII_XML_10,
    VID_TAXII_SERVICES_10, VID_TAXII_SERVICES_11
)

from .http import (
    HTTP_X_TAXII_ACCEPT, HTTP_X_TAXII_CONTENT_TYPE,
    get_http_headers
)


def process_status_exception(exception, headers, is_secure):

    accepted_content = headers.get(HTTP_X_TAXII_ACCEPT)

    # No accepted_content provided, so try to use
    # X-TAXII-Content-Type header
    if not accepted_content:
        accepted_content = headers.get(HTTP_X_TAXII_CONTENT_TYPE)

    try:
        status = exception_to_status(exception, accepted_content)
    except ValueError:
        status = exception_to_status(exception, VID_TAXII_XML_11)

    if accepted_content == VID_TAXII_XML_10:
        version = VID_TAXII_SERVICES_10
    elif accepted_content == VID_TAXII_XML_11:
        version = VID_TAXII_SERVICES_11
    else:
        # Unknown accepted content.
        # Pretending X-TAXII-Accept was TAXII 1.1
        version = VID_TAXII_SERVICES_11

    response_headers = get_http_headers(version, is_secure)

    return status.to_xml(pretty_print=True), response_headers


def exception_to_status(exception, format_version):

    data = dict(
        message_id=generate_message_id(),
        in_response_to=exception.in_response_to,
        extended_headers=exception.extended_headers,
        status_type=exception.status_type,
        status_detail=exception.status_details,
        message=exception.message
    )

    if format_version == VID_TAXII_XML_11:
        sm = tm11.StatusMessage(**data)
    elif format_version == VID_TAXII_XML_10:
        sm = tm10.StatusMessage(**data)
    else:
        raise ValueError("Unknown version: %s" % format_version)

    return sm
