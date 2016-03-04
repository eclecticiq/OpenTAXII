import structlog

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import ST_SUCCESS

from .base_handlers import BaseMessageHandler
from ...exceptions import raise_failure
from ...converters import (
    inbox_message_to_inbox_message_entity,
    content_block_to_content_block_entity
)

log = structlog.getLogger(__name__)


class InboxMessage11Handler(BaseMessageHandler):

    supported_request_messages = [tm11.InboxMessage]

    @classmethod
    def handle_message(cls, service, request):

        collections = service.validate_destination_collection_names(
            request.destination_collection_names, request.message_id)

        inbox_message = service.server.persistence.create_inbox_message(
            inbox_message_to_inbox_message_entity(
                request, service_id=service.id, version=11))

        for content_block in request.content_blocks:

            is_supported = service.is_content_supported(
                content_block.content_binding, version=11)

            # FIXME: is it correct to skip unsupported content blocks?
            # 3.2 Inbox Exchange
            # version1.1/TAXII_Services_Specification.pdf
            if not is_supported:
                log.warning("Content binding is not supported: {}"
                            .format(content_block.content_binding))
                continue

            supporting_collections = []
            for collection in collections:

                if collection.is_content_supported(
                        content_block.content_binding):

                    supporting_collections.append(collection)

            if len(supporting_collections) == 0 and not is_supported:
                # There's nothing to add this content block to
                log.warning("No collection that support binding {} were found"
                            .format(content_block.content_binding))
                continue

            block = content_block_to_content_block_entity(
                content_block, version=11)

            service.server.persistence.create_content(
                block,
                collections=supporting_collections,
                service_id=service.id,
                inbox_message_id=inbox_message.id if inbox_message else None)

        # Create and return a Status Message indicating success
        status_message = tm11.StatusMessage(
            message_id=cls.generate_id(),
            in_response_to=request.message_id,
            status_type=ST_SUCCESS
        )

        return status_message


class InboxMessage10Handler(BaseMessageHandler):

    supported_request_messages = [tm10.InboxMessage]

    @classmethod
    def handle_message(cls, service, request):

        collections = service.get_destination_collections()

        inbox_message = service.server.persistence.create_inbox_message(
            inbox_message_to_inbox_message_entity(
                request, service_id=service.id, version=10))

        for content_block in request.content_blocks:

            is_supported = service.is_content_supported(
                content_block.content_binding, version=10)

            if not is_supported:
                log.warning("Content block binding is not supported: {}"
                            .format(content_block.content_binding))
                continue

            block = content_block_to_content_block_entity(
                content_block, version=10)

            service.server.persistence.create_content(
                block, collections=collections,
                service_id=service.id,
                inbox_message_id=inbox_message.id if inbox_message else None)

        status_message = tm10.StatusMessage(
            message_id=cls.generate_id(),
            in_response_to=request.message_id,
            status_type=ST_SUCCESS
        )

        return status_message


class InboxMessageHandler(BaseMessageHandler):

    supported_request_messages = [tm10.InboxMessage, tm11.InboxMessage]

    @classmethod
    def handle_message(cls, service, request):
        if isinstance(request, tm10.InboxMessage):
            return InboxMessage10Handler.handle_message(service, request)
        elif isinstance(request, tm11.InboxMessage):
            return InboxMessage11Handler.handle_message(service, request)
        else:
            raise_failure("TAXII Message not supported by message handler",
                          request.message_id)
