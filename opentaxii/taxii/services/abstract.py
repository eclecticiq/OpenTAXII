import structlog
import hashlib

from libtaxii.common import generate_message_id
from libtaxii.constants import (
    VID_TAXII_XML_10, VID_TAXII_XML_11,
    VID_TAXII_HTTPS_10
)

from ..exceptions import StatusMessageException, raise_failure
from ..bindings import PROTOCOL_TO_SCHEME
from ..converters import service_to_service_instances


class TaxiiService(object):

    id = None
    description = 'Default TAXII service description'
    enabled = True

    server = None

    authentication_required = False

    supported_message_bindings = [VID_TAXII_XML_10, VID_TAXII_XML_11]
    supported_protocol_bindings = [VID_TAXII_HTTPS_10]

    def __init__(self, id, server, address, description=None,
            protocol_bindings=None, enabled=True, authentication_required=False):

        self.id = id
        self.server = server
        self.address = address
        self.description = description
        self.supported_protocol_bindings = protocol_bindings or self.supported_protocol_bindings

        self.enabled = enabled
        self.authentication_required = authentication_required

        self.log = structlog.getLogger("%s.%s" % (self.__module__,
            self.__class__.__name__), service_id=id)


    def generate_id(self):
        return generate_message_id()


    def process(self, headers, message):

        self.log.info("Processing message", message_id=message.message_id,
                message_type=message.message_type, message_version=message.version)

        handler = self.get_message_handler(message)

        handler.validate_headers(headers, in_response_to=message.message_id)
        handler.verify_message_is_supported(message)

        try:
            response_message = handler.handle_message(self, message)
        except StatusMessageException:
            raise
        except Exception:
            raise_failure("There was a failure while executing the message handler",
                    in_response_to=message.message_id)

        if not response_message:
            raise_failure("The message handler %s did not return a TAXII Message" % handler,
                    in_response_to=message.message_id)

        return response_message


    def get_message_handler(self, message):
        try:
            return self.handlers[message.message_type]
        except KeyError:
            self.log.warning("Message not supported", message_id=message.message_id,
                    message_type=message.message_type, message_version=message.version)
            raise_failure("Message not supported by this service",
                    in_response_to=message.message_id)


    def to_service_instances(self, version):
        return service_to_service_instances(self, version)


    @property
    def uid(self):
        return hashlib.md5(self.id + self.address).hexdigest() 


    def absolute_address(self, binding):
        address = self.address

        if binding in PROTOCOL_TO_SCHEME:
            scheme = PROTOCOL_TO_SCHEME[binding]
            if scheme and not address.startswith(scheme):
                address = scheme + address

        return address


    def __repr__(self):
        return "%s(id=%s, address=%s)" % (self.__class__.__name__, self.id, self.address)



