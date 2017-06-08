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

    @classmethod
    def verify_content_is_valid(cls, content, content_binding):
        # If the content binding isn't something we support, then raise a failure
        if content_binding not in CONTENT_BINDINGS:
            raise raise_failure(
                "OpenTAXII does not support the {} content binding".format(content_binding),
                taxii_message.message_id)

        print ("taxii 1.1 content_block content:{}\n".format(content_block.content))
        # Validate that the STIX content is actually STIX content with the STIX Validator
        #results = sdv.validate_xml('stix-content.xml', version='1.2')
        try:
            # Prepare the content block for processing by the STIX data validator
            content_block_to_validate  = StringIO.StringIO()
            content_block_to_validate.write(content_block.content)
            # Run the STIX data validator with the correct content binding
            # Eliminates the chance of a client sending the wrong STIX file with the
            # wrong content_binding.
            if content_binding == CB_STIX_XML_10:
                results = sdv.validate_xml(content_block_to_validate, '1.0')
            elif content_binding == CB_STIX_XML_101:
                results = sdv.validate_xml(content_block_to_validate, '1.0.1')
            elif content_binding == CB_STIX_XML_11:
                results = sdv.validate_xml(content_block_to_validate, '1.1')
            elif content_binding == CB_STIX_XML_111:
                results = sdv.validate_xml(content_block_to_validate, '1.1.1')
            elif content_binding == CB_STIX_XML_12:
                results = sdv.validate_xml(content_block_to_validate, '1.2')
            else:
                # Should never get here, but just in case...
                raise raise_failure(
                        "OpenTAXII does not support the {} content binding".format(content_binding),
                        taxii_message.message_id)
            content_block_to_validate.close()
            # Test the results of the validator to make sure the schema is valid
            if not results.is_valid:
                failure = True
                failure_message = "The TAXII message {} contains invalid STIX content in one of the content blocks ({}).".format(request.message_id,content_block.content_binding)
                raise raise_failure(
                    failure_message,
                    taxii_message.message_id)
                return False
                
        except Exception as ve:
            # In some instances the validator can raise an exception. This copes with this fact
            failure = True
            failure_message = "The TAXII message {} contains invalid STIX content in one of the content blocks ({}).".format(request.message_id,content_block.content_binding)
            raise raise_failure(
                failure_message,
                taxii_message.message_id)
            return False
            
        return True
