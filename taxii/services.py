import libtaxii

from libtaxii.constants import *

from .handlers import *
from .bindings import CONTENT_BINDINGS, PROTOCOL_BINDINGS

from .exceptions import StatusMessageException, raise_failure

from urlparse import urlparse
from taxii.http import verify_headers_and_parse

class _TaxiiService(object):

    supported_message_bindings = []
    supported_protocol_bindings = []
    enabled = False

    supported_protocol_bindings = PROTOCOL_BINDINGS

    def __init__(self, full_path):
        self.full_path = full_path

    def get_path(self):
        return urlparse(self.full_path).path


    def view(self, headers, body, is_secure=False):

        taxii_message = verify_headers_and_parse(headers, body)

        handler = self.get_message_handler(taxii_message)

        handler.validate_headers(headers, in_response_to=taxii_message.message_id)
        handler.validate_message_is_supported(taxii_message)

        try:
            response_message = handler.handle_message(self, taxii_message)
        except StatusMessageException:
            raise
        except Exception as e:  # Something else happened
            message = "There was a failure while executing the message handler"
            raise_failure(message, in_response_to=taxii_message.message_id)

        if not response_message:
            message = "The message handler %s did not return a TAXII Message" % handler
            raise_failure(None, in_response_to=taxii_message.message_id)

        response_headers = get_headers(response_message, is_secure)

        return response_message.to_xml(pretty_print=True), response_headers



    def get_message_handler(self, taxii_message):
        try:
            return self.handlers[taxii_message.message_type]
        except KeyError:
            raise StatusMessageException(ST_FAILURE, message="Message not supported by this service", in_response_to=taxii_message.message_id)



class CollectionManagementService(_TaxiiService):

    requests = [libtaxii.messages_10.FeedInformationRequest, libtaxii.messages_11.CollectionInformationRequest]

    handlers = {
        MSG_COLLECTION_INFORMATION_REQUEST : CollectionInformationRequestHandler,
        MSG_FEED_INFORMATION_REQUEST : CollectionInformationRequestHandler,

        MSG_MANAGE_COLLECTION_SUBSCRIPTION_REQUEST : SubscriptionRequestHandler,
        MSG_MANAGE_FEED_SUBSCRIPTION_REQUEST : SubscriptionRequestHandler
    }
            
    service_type = SVC_COLLECTION_MANAGEMENT

    supported_queries = []

    def get_advertised_collections(self):
        return []


class DiscoveryService(_TaxiiService):

    service_type = SVC_DISCOVERY

    handlers = {
        MSG_DISCOVERY_REQUEST : DiscoveryRequestHandler
    }

    def __init__(self, full_path, services=[]):
        super(DiscoveryService, self).__init__(full_path)
        self.services = services

    def get_advertised_services(self):
        return self.services




class InboxService(_TaxiiService):

    service_type = SVC_INBOX

    handlers = {
        MSG_INBOX_MESSAGE : InboxMessageHandler
    }

    destination_collection_specification = 'REQUIRED' # PROHIBITED

    destination_collections = dict()

    accept_all_content = False

    supported_content = CONTENT_BINDINGS


    def is_content_supported(self, content_binding):

        if self.accept_all_content:
            return True

        matches = [
            ((supported.main == content_binding.main) and (not supported.subtype or supported.subtype == content_binding.subtype)) \
            for supported in self.supported_content
        ]

        return any(matches)


    def validate_destination_collection_names(self, name_list, in_response_to):
        """
        Returns:
            A list of Data Collections

        Raises:
            A StatusMessageException if any Destination Collection Names are invalid.
        """

        name_list = name_list or []

        if (self.destination_collection_specification == 'REQUIRED' and not name_list) or \
                (self.destination_collection_specification == 'PROHIBITED' and name_list):

            exc = StatusMessageException(ST_DESTINATION_COLLECTION_ERROR, in_response_to=in_response_to,
                    extended_headers = {SD_ACCEPTABLE_DESTINATION: [k for (k, v) in self.destination_collections.items() if v.enabled]})

            if not name_list:
                exc.message = 'A Destination_Collection_Name is required and none were specified'
            else:
                exc.message = 'Destination_Collection_Names are prohibited for this Inbox Service'

            raise exc


        collections = []

        for name in name_list:
            try:
                collections.append(self.destination_collections[name])
            except KeyError:
                raise StatusMessageException(ST_NOT_FOUND, message='The Data Collection was not found',
                        in_response_to=in_response_to, extended_headers={SD_ITEM: name})

        return collections


    def to_service_instances(self, v=10):

        service_instances = to_service_instances(self, v)

        if self.accept_all_content:
            return service_instances

        for si in service_instances:
            si.accepted_contents = self.get_supported_content(v)

        return service_instances


    def get_supported_content(self, v=10):

        if self.accept_all_content:
            return  # Indicates accept all


        return_list = []

        if v == 10:
            for content in self.supported_content.all():
                return_list.append(content.content_binding.binding_id)

        elif v == 11:
            supported_content = {}

            for content in self.supported_content.all():
                binding_id = content.content_binding.binding_id
                subtype = content.subtype
                if binding_id not in supported_content:
                    supported_content[binding_id] = tm11.ContentBinding(binding_id=binding_id)

                if subtype and subtype.subtype_id not in supported_content[binding_id].subtype_ids:
                    supported_content[binding_id].subtype_ids.append(subtype.subtype_id)

            return_list = supported_content.values()

        return return_list
