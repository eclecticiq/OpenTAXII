import hashlib

from libtaxii.constants import VID_TAXII_XML_10, VID_TAXII_XML_11

from ..exceptions import StatusMessageException, raise_failure
from ..transform import service_to_instances


class TaxiiService(object):

    id = None
    description = None
    enabled = True

    server = None

    supported_message_bindings = [VID_TAXII_XML_10, VID_TAXII_XML_11]
    supported_protocol_bindings = []

    def __init__(self, id, server, address, description=None, protocol_bindings=[]):
        self.id = id
        self.server = server
        self.address = address
        self.description = description
        self.supported_protocol_bindings = protocol_bindings


    def process(self, headers, taxii_message):


        handler = self.get_message_handler(taxii_message)

        handler.validate_headers(headers, in_response_to=taxii_message.message_id)
        handler.verify_message_is_supported(taxii_message)

        try:
            response_message = handler.handle_message(self, taxii_message)
        except StatusMessageException:
            raise
        except Exception as e:
            raise_failure("There was a failure while executing the message handler",
                    in_response_to=taxii_message.message_id)

        if not response_message:
            raise_failure("The message handler %s did not return a TAXII Message" % handler,
                    in_response_to=taxii_message.message_id)

        return response_message


    def get_message_handler(self, taxii_message):
        try:
            return self.handlers[taxii_message.message_type]
        except KeyError:
            raise_failure("Message not supported by this service",
                    in_response_to=taxii_message.message_id)


    def to_service_instances(self, version):
        return service_to_instances(self, version)


    @property
    def uid(self):
        return hashlib.md5(self.id + self.address).hexdigest() 


    def __repr__(self):
        return "%s(id=%s, address=%s)" % (self.__class__.__name__, self.id, self.address)



