from libtaxii.constants import (
    VID_TAXII_XML_10, VID_TAXII_XML_11,
    VID_TAXII_SERVICES_10, VID_TAXII_SERVICES_11
)
from libtaxii.common import generate_message_id

from ...exceptions import raise_failure
from ...http import (
    HTTP_X_TAXII_CONTENT_TYPE, HTTP_X_TAXII_SERVICES, HTTP_X_TAXII_ACCEPT)


class BaseMessageHandler(object):

    supported_request_messages = []

    @staticmethod
    def generate_id():
        return generate_message_id()

    @classmethod
    def validate_headers(cls, headers, in_response_to=None):

        taxii_content_type = headers[HTTP_X_TAXII_CONTENT_TYPE]
        taxii_services = headers[HTTP_X_TAXII_SERVICES]
        taxii_accept = headers.get(HTTP_X_TAXII_ACCEPT)

        # Identify which TAXII versions the message handler supports
        supports_taxii_11 = False
        supports_taxii_10 = False

        for message in cls.supported_request_messages:
            if message.version == VID_TAXII_XML_11:
                supports_taxii_11 = True
            elif message.version == VID_TAXII_XML_10:
                supports_taxii_10 = True
            else:
                raise ValueError(
                    'The variable "supported_request_messages" '
                    'contained a non-libtaxii message module: {}'.
                    format(message.__module__))

        no_support_service_11 = (
            taxii_services == VID_TAXII_SERVICES_11 and not supports_taxii_11)

        no_support_service_10 = (
            taxii_services == VID_TAXII_SERVICES_10 and not supports_taxii_10)

        if no_support_service_11 or no_support_service_10:
            raise_failure(
                'The specified value of {} is not supported'.format(
                    HTTP_X_TAXII_SERVICES),
                in_response_to)

        no_support_content_type_11 = (
            taxii_content_type == VID_TAXII_XML_11 and not supports_taxii_11)
        no_support_content_type_10 = (
            taxii_content_type == VID_TAXII_XML_10 and not supports_taxii_10)

        if no_support_content_type_11 or no_support_content_type_10:
            raise_failure(
                'The specified value of X-TAXII-Content-Type is not supported',
                in_response_to)

        no_support_accept_11 = (
            taxii_accept == VID_TAXII_XML_11 and not supports_taxii_11)
        no_support_accept_10 = (
            taxii_accept == VID_TAXII_XML_10 and not supports_taxii_10)

        if taxii_accept and (no_support_accept_11 or no_support_accept_10):
            raise_failure(
                "The specified value of X-TAXII-Accept is not supported",
                in_response_to)

        return True

    @classmethod
    def verify_message_is_supported(cls, taxii_message):
        if taxii_message.__class__ not in cls.supported_request_messages:
            raise raise_failure(
                "TAXII Message not supported by Message Handler",
                taxii_message.message_id)

    @classmethod
    def handle_message(cls, service, request):
        raise NotImplementedError()
