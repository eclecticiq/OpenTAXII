import libtaxii

from libtaxii.constants import *
import libtaxii.messages_11 as tm11

from .transform import *
from .bindings import CONTENT_BINDINGS, HTTP_PROTOCOL_BINDINGS

from .exceptions import StatusMessageException, raise_failure
from .http import verify_headers_and_parse
from .handlers import *
from .utils import is_content_supported

from persistence.managers import DataCollectionManager

class TaxiiService(object):

    supported_message_bindings = []
    supported_protocol_bindings = []
    enabled = True

    supported_protocol_bindings = HTTP_PROTOCOL_BINDINGS

    def __init__(self, full_path):
        self.full_path = full_path

    def get_path(self):
        return "/" + self.full_path.split('/', 1)[1]   # nasty, but we don't have schema here, so urlparse is useless


    def view(self, headers, body):

        taxii_message = verify_headers_and_parse(headers, body)

        handler = self.get_message_handler(taxii_message)

        handler.validate_headers(headers, in_response_to=taxii_message.message_id)
        handler.validate_message_is_supported(taxii_message)

        try:
            response_message = handler.handle_message(self, taxii_message)
        except StatusMessageException:
            raise
        except Exception as e:  # Something else happened
            raise_failure("There was a failure while executing the message handler", in_response_to=taxii_message.message_id)

        if not response_message:
            raise_failure("The message handler %s did not return a TAXII Message" % handler, in_response_to=taxii_message.message_id)

        return response_message



    def get_message_handler(self, taxii_message):
        try:
            return self.handlers[taxii_message.message_type]
        except KeyError:
            raise StatusMessageException(ST_FAILURE, message="Message not supported by this service", in_response_to=taxii_message.message_id)


    def to_service_instances(self, version):
        return to_service_instances(self, version)


class CollectionManagementService(TaxiiService):

    requests = [libtaxii.messages_10.FeedInformationRequest, libtaxii.messages_11.CollectionInformationRequest]

    handlers = {
        MSG_COLLECTION_INFORMATION_REQUEST : CollectionInformationRequestHandler,
        MSG_FEED_INFORMATION_REQUEST : CollectionInformationRequestHandler,

        MSG_MANAGE_COLLECTION_SUBSCRIPTION_REQUEST : SubscriptionRequestHandler,
        MSG_MANAGE_FEED_SUBSCRIPTION_REQUEST : SubscriptionRequestHandler
    }
            
    service_type = SVC_COLLECTION_MANAGEMENT

    supported_queries = []

    description = 'CollectionManagementService description'

    def get_advertised_collections(self):
        return []


class DiscoveryService(TaxiiService):

    service_type = SVC_DISCOVERY

    handlers = {
        MSG_DISCOVERY_REQUEST : DiscoveryRequestHandler
    }

    description = 'DiscoveryService description'

    def __init__(self, full_path, services=[]):
        super(DiscoveryService, self).__init__(full_path)
        self.services = services

    def get_advertised_services(self):
        return self.services + [self]




class InboxService(TaxiiService):

    id = 'inbox-service-1'

    service_type = SVC_INBOX

    handlers = {
        MSG_INBOX_MESSAGE : InboxMessageHandler
    }

    destination_collection_specification = 'REQUIRED' # PROHIBITED

    accept_all_content = True

    supported_content = CONTENT_BINDINGS

    description = 'InboxService description'


    def is_content_supported(self, content_binding, version=None):

        if self.accept_all_content:
            return True

        return is_content_supported(self.supported_content, content_binding, version=version)


    def get_destination_collections(self):
        return DataCollectionManager.get_all_collections()


    def validate_destination_collection_names(self, name_list, in_response_to):

        name_list = name_list or []

        if (self.destination_collection_specification == 'REQUIRED' and not name_list) or \
                (self.destination_collection_specification == 'PROHIBITED' and name_list):

            if not name_list:
                message = 'A Destination_Collection_Name is required and none were specified'
            else:
                message = 'Destination_Collection_Names are prohibited for this Inbox Service'

            exc = StatusMessageException(ST_DESTINATION_COLLECTION_ERROR, message=message, in_response_to=in_response_to,
                    extended_headers = {SD_ACCEPTABLE_DESTINATION: [c.name for c in self.get_destination_collections() if c.enabled]})

            raise exc

        collections = []

        destinations_map = dict((c.name, c) for c in self.get_destination_collections())

        for name in name_list:
            if name in destinations_map:
                collections.append(destinations_map[name])
            else:
                raise StatusMessageException(ST_NOT_FOUND, message='The Data Collection was not found',
                        in_response_to=in_response_to, extended_headers={SD_ITEM: name})

        return collections


    def to_service_instances(self, version):

        service_instances = to_service_instances(self, version)

        if self.accept_all_content:
            return service_instances

        for si in service_instances:
            si.inbox_service_accepted_content = self.get_supported_content(version)

        return service_instances


    def get_supported_content(self, version):

        if self.accept_all_content:
            return  # Indicates accept all

        return_list = []

        if version == 10:
            for content in self.supported_content:
                return_list.append(content.binding)

        elif version == 11:
            supported_content = {}

            for content in self.supported_content:
                if content.binding not in supported_content:
                    supported_content[content.binding] = tm11.ContentBinding(binding_id=content.binding, subtype_ids=content.subtypes)

            return_list = supported_content.values()

        return return_list

