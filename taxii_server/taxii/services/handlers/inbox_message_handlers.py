
import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import *

from ...exceptions import StatusMessageException, raise_failure
from ...entities import InboxMessageEntity, ContentBlockEntity, ContentBindingEntity
from .base_handlers import BaseMessageHandler

import structlog
log = structlog.getLogger(__name__)

class InboxMessage11Handler(BaseMessageHandler):

    supported_request_messages = [tm11.InboxMessage]

    @classmethod
    def handle_message(cls, inbox_service, inbox_message):

        collections = inbox_service.validate_destination_collection_names(
                inbox_message.destination_collection_names, inbox_message.message_id)

        message = to_inbox_message_entity(inbox_message, version=11)

        message = inbox_service.server.data_manager.save_inbox_message(message,
                service_id=inbox_service.id)

        for content_block in inbox_message.content_blocks:

            is_supported = inbox_service.is_content_supported(content_block.content_binding, version=11)

            # FIXME: is it correct to skip unsupported content blocks?
            # 3.2 Inbox Exchange, http://taxii.mitre.org/specifications/version1.1/TAXII_Services_Specification.pdf
            if not is_supported:
                log.warning("Content block binding is not supported: %s", content_block.content_binding)
                continue

            supporting_collections = []
            for collection in collections:
                supported_by_collection = collection.is_content_supported(content_block.content_binding)
                if supported_by_collection:
                    supporting_collections.append(collection)

            if len(supporting_collections) == 0 and not is_supported:
                # There's nothing to add this content block to
                log.warning("No collection that support binding %s were found", content_block.content_binding)
                continue

            block = to_content_block_entity(content_block, inbox_message_entity=message, version=11)

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
    """
    Built in TAXII 1.0 Message Handler
    """
    supported_request_messages = [tm10.InboxMessage]

    @classmethod
    def handle_message(cls, inbox_service, inbox_message):

        collections = inbox_service.get_destination_collections()

        message = to_inbox_message_entity(inbox_message, version=10)

        message = inbox_service.server.data_manager.save_inbox_message(message,
                service_id=inbox_service.id)

        for content_block in inbox_message.content_blocks:
            is_supported = inbox_service.is_content_supported(content_block.content_binding, version=10)

            if not is_supported:
                log.warning("Content block binding is not supported: %s", content_block.content_binding)
                continue

            block = to_content_block_entity(content_block, inbox_message_entity=message, version=10)

            inbox_service.server.data_manager.save_content(block, inbox_message_entity=message,
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
            raise_failure("TAXII Message not supported by message handler", inbox_message.message_id)





def to_inbox_message_entity(inbox_message, version):

    params = dict(
        message_id = inbox_message.message_id,
        original_message = inbox_message.to_xml(), #FIXME: raw?
        content_block_count = len(inbox_message.content_blocks),
    )

    if version == 10:

        if inbox_message.subscription_information:
            si = inbox_message.subscription_information
            params.update(dict(
                subscription_collection_name = si.feed_name,
                subscription_id = si.subscription_id,

                # TODO: Match up exclusive vs inclusive
                exclusive_begin_timestamp_label = si.inclusive_begin_timestamp_label,
                inclusive_end_timestamp_label = si.inclusive_end_timestamp_label,
            ))

    elif version == 11:

        params.update(dict(
            result_id = inbox_message.result_id,
            destination_collections = inbox_message.destination_collection_names,
        ))

        if inbox_message.record_count:
            params.update(dict(
                record_count = inbox_message.record_count.record_count,
                partial_count = inbox_message.record_count.partial_count
            ))

        if inbox_message.subscription_information:
            si = inbox_message.subscription_information
            params.update(dict(
                subscription_collection_name = si.collection_name,
                subscription_id = si.subscription_id,

                exclusive_begin_timestamp_label = si.exclusive_begin_timestamp_label,
                inclusive_end_timestamp_label = si.inclusive_end_timestamp_label
            ))


    return InboxMessageEntity(**params)


def to_content_block_entity(content_block, inbox_message_entity, version):

    if version == 10:
        content_binding = ContentBindingEntity(
            binding = content_block.content_binding,
            subtypes = None
        )
        message = None

    elif version == 11:

        content_binding = ContentBindingEntity(
            binding = content_block.content_binding.binding_id,
            subtypes = content_block.content_binding.subtype_ids
        )
        message = content_block.message

    # TODO: What about signatures?
    return ContentBlockEntity(
        id = None,
        message = message,
        inbox_message_id = inbox_message_entity.id,
        content = content_block.content,
        timestamp_label = content_block.timestamp_label,
        content_binding = content_binding
        # padding = content_block.padding,
    )

