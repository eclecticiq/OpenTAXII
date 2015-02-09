
import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import *

from ...exceptions import StatusMessageException, raise_failure
from ...entities import InboxMessageEntity, ContentBlockEntity
from .base_handlers import BaseMessageHandler


class InboxMessage11Handler(BaseMessageHandler):

    supported_request_messages = [tm11.InboxMessage]

    @classmethod
    def handle_message(cls, inbox_service, inbox_message):

        collections = inbox_service.validate_destination_collection_names(
                inbox_message.destination_collection_names, inbox_message.message_id)

        message = InboxMessageEntity.to_entity(inbox_message,
                received_via=inbox_service.id, version=11)

        message = inbox_service.server.storage.save_inbox_message(message)

        for content_block in inbox_message.content_blocks:

            is_supported = inbox_service.is_content_supported(content_block.content_binding, version=11)

            # FIXME: is it correct to skip unsupported content blocks?
            # 3.2 Inbox Exchange, http://taxii.mitre.org/specifications/version1.1/TAXII_Services_Specification.pdf
            if not is_supported:
                continue

            supporting_collections = []
            for collection in collections:
                supported_by_collection = collection.is_content_supported(content_block.content_binding)
                if supported_by_collection:
                    supporting_collections.append(collection)

            if len(supporting_collections) == 0 and not is_supported:
                # There's nothing to add this content block to
                continue

            block = ContentBlockEntity.to_entity(content_block, inbox_message_entity=message, version=11)

            inbox_service.server.storage.save_content_block(block, inbox_message_entity=message,
                    collections=supporting_collections)


        # Create and return a Status Message indicating success
        status_message = tm11.StatusMessage(
            message_id = cls.generate_id(),
            in_response_to = inbox_message.message_id,
            status_type = ST_SUCCESS
        )

        return status_message


class InboxMessage10Handler(BaseMessageHandler):
    """
    Built in TAXII 1.0 Message Handler
    """
    supported_request_messages = [tm10.InboxMessage]

    @classmethod
    def handle_message(cls, inbox_service, inbox_message):

        collections = inbox_service.get_destination_collections()

        message = InboxMessageEntity.to_entity(inbox_message,
                received_via=inbox_service.id, version=10)
        message = inbox_service.server.storage.save_inbox_message(message)

        for content_block in inbox_message.content_blocks:
            is_supported = inbox_service.is_content_supported(content_block.content_binding, version=10)

            if not is_supported:
                continue

            block = ContentBlockEntity.to_entity(content_block, inbox_message_entity=message, version=10)

            inbox_service.server.storage.save_content_block(block, inbox_message_entity=message,
                    collections=collections)


        status_message = tm10.StatusMessage(
            message_id = cls.generate_id(),
            in_response_to = inbox_message.message_id,
            status_type = ST_SUCCESS
        )

        return status_message


class InboxMessageHandler(BaseMessageHandler):
    """
    Built-in TAXII 1.1 and 1.0 Message Handler
    """
    supported_request_messages = [tm10.InboxMessage, tm11.InboxMessage]

    @staticmethod
    def handle_message(inbox_service, inbox_message):
        if isinstance(inbox_message, tm10.InboxMessage):
            return InboxMessage10Handler.handle_message(inbox_service, inbox_message)
        elif isinstance(inbox_message, tm11.InboxMessage):
            return InboxMessage11Handler.handle_message(inbox_service, inbox_message)
        else:
            raise_failure("TAXII Message not supported by Message Handler", inbox_message.message_id)
