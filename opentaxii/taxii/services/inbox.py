
from libtaxii.constants import (
    SVC_INBOX, MSG_INBOX_MESSAGE, SD_ACCEPTABLE_DESTINATION,
    ST_DESTINATION_COLLECTION_ERROR, ST_NOT_FOUND, SD_ITEM
)

from ..utils import is_content_supported
from ..entities import ContentBindingEntity
from ..exceptions import StatusMessageException

from ..converters import (
    content_binding_entities_to_content_bindings,
    service_to_service_instances
)

from .abstract import TAXIIService
from .handlers import InboxMessageHandler


class InboxService(TAXIIService):

    service_type = SVC_INBOX

    handlers = {
        MSG_INBOX_MESSAGE: InboxMessageHandler
    }

    destination_collection_required = False
    accept_all_content = False
    supported_content = []

    def __init__(self, accept_all_content=False,
                 destination_collection_required=False,
                 supported_content=None, **kwargs):

        super(InboxService, self).__init__(**kwargs)

        self.accept_all_content = accept_all_content

        supported_content = supported_content or []
        self.supported_content = [
            ContentBindingEntity(c) for c in supported_content]

        self.destination_collection_required = destination_collection_required

    def is_content_supported(self, content_binding, version=None):

        if self.accept_all_content:
            return True

        return is_content_supported(self.supported_content, content_binding,
                                    version=version)

    def get_destination_collections(self):
        return self.server.persistence.get_collections(self.id)

    def validate_destination_collection_names(self, name_list, in_response_to):

        name_list = name_list or []

        if (self.destination_collection_required and not name_list) or \
                (not self.destination_collection_required and name_list):

            if not name_list:
                message = ('A Destination_Collection_Name is required '
                           'and none were specified')
            else:
                message = ('Destination_Collection_Names are prohibited '
                           'for this Inbox Service')

            details = {
                SD_ACCEPTABLE_DESTINATION: [
                    c.name for c in self.get_destination_collections()
                    if c.available
                ]
            }

            raise StatusMessageException(
                ST_DESTINATION_COLLECTION_ERROR,
                message=message,
                in_response_to=in_response_to,
                extended_headers=details)

        if not name_list:
            return []

        collections = []

        destinations_map = {c.name: c
                            for c in self.get_destination_collections()}

        for name in name_list:
            if name in destinations_map:
                collections.append(destinations_map[name])
            else:
                raise StatusMessageException(
                    ST_NOT_FOUND,
                    message='The Data Collection was not found',
                    in_response_to=in_response_to,
                    extended_headers={SD_ITEM: name})

        return collections

    def to_service_instances(self, version):

        service_instances = service_to_service_instances(self, version)

        if self.accept_all_content:
            return service_instances

        for instance in service_instances:
            instance.inbox_service_accepted_content = (
                self.get_supported_content(version))

        return service_instances

    def get_supported_content(self, version):

        if self.accept_all_content:
            return []

        return content_binding_entities_to_content_bindings(
            self.supported_content, version)
