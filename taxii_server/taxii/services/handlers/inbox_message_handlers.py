
import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import *

from ...exceptions import StatusMessageException, raise_failure
from ...entities import InboxMessageEntity, ContentBlockEntity, ContentBindingEntity
from .base_handlers import BaseMessageHandler

from ...converters import inbox_message_to_inbox_message_entity, content_block_to_content_block_entity

import structlog
log = structlog.getLogger(__name__)

class InboxMessage11Handler(BaseMessageHandler):

    supported_request_messages = [tm11.InboxMessage]

    @classmethod
    def handle_message(cls, inbox_service, inbox_message):

        collections = inbox_service.validate_destination_collection_names(
                inbox_message.destination_collection_names, inbox_message.message_id)

        message = inbox_message_to_inbox_message_entity(inbox_message, version=11)

        message = inbox_service.server.data_manager.save_inbox_message(message,
                service_id=inbox_service.id)

        for content_block in inbox_message.content_blocks:

            is_supported = inbox_service.is_content_supported(content_block.content_binding, version=11)

            # FIXME: is it correct to skip unsupported content blocks?
            # 3.2 Inbox Exchange, http://taxii.mitre.org/specifications/version1.1/TAXII_Services_Specification.pdf
            if not is_supported:
                log.warning("Content block binding is not supported: %s" % content_block.content_binding)
                continue

            supporting_collections = []
            for collection in collections:
                supported_by_collection = collection.is_content_supported(content_block.content_binding)
                if supported_by_collection:
                    supporting_collections.append(collection)

            if len(supporting_collections) == 0 and not is_supported:
                # There's nothing to add this content block to
                log.warning("No collection that support binding %s were found" % content_block.content_binding)
                continue

            block = content_block_to_content_block_entity(content_block, inbox_message_entity=message, version=11)

            inbox_service.server.data_manager.save_content(block, inbox_message_entity=message,
                    collections=supporting_collections)


        # Create and return a Status Message indicating success
        status_message = tm11.StatusMessage(
            message_id = cls.generate_id(),
            in_response_to = inbox_message.message_id,
            status_type = ST_SUCCESS
        )

        return status_message


class InboxMessage10Handler(BaseMessageHandler):

    supported_request_messages = [tm10.InboxMessage]

    @classmethod
    def handle_message(cls, inbox_service, inbox_message):

        collections = inbox_service.get_destination_collections()

        message = inbox_message_to_inbox_message_entity(inbox_message, version=10)

        message = inbox_service.server.data_manager.save_inbox_message(message,
                service_id=inbox_service.id)

        for content_block in inbox_message.content_blocks:
            is_supported = inbox_service.is_content_supported(content_block.content_binding, version=10)

            if not is_supported:
                log.warning("Content block binding is not supported: %s" % content_block.content_binding)
                continue

            block = content_block_to_content_block_entity(content_block, inbox_message_entity=message, version=10)

            inbox_service.server.data_manager.save_content(block, inbox_message_entity=message,
                    collections=collections)

        status_message = tm10.StatusMessage(
            message_id = cls.generate_id(),
            in_response_to = inbox_message.message_id,
            status_type = ST_SUCCESS
        )

        return status_message


class InboxMessageHandler(BaseMessageHandler):

    supported_request_messages = [tm10.InboxMessage, tm11.InboxMessage]

    @staticmethod
    def handle_message(inbox_service, inbox_message):
        if isinstance(inbox_message, tm10.InboxMessage):
            return InboxMessage10Handler.handle_message(inbox_service, inbox_message)
        elif isinstance(inbox_message, tm11.InboxMessage):
            return InboxMessage11Handler.handle_message(inbox_service, inbox_message)
        else:
            raise_failure("TAXII Message not supported by message handler", inbox_message.message_id)

