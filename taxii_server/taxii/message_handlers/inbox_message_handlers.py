# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import *
from libtaxii.common import generate_message_id

from .base_handlers import BaseMessageHandler
from ..exceptions import StatusMessageException, raise_failure

class InboxMessage11Handler(BaseMessageHandler):
    """
    Built-in TAXII 1.1 Inbox Message Handler.
    """

    supported_request_messages = [tm11.InboxMessage]

    @classmethod
    def handle_message(cls, inbox_service, inbox_message):

        collections = inbox_service.validate_destination_collection_names(
                inbox_message.destination_collection_names, inbox_message.message_id)

        blocks = []
        saved_blocks = 0

        inbox_message_entity = inbox_service.server.storage.save_inbox_message(inbox_message, received_via=inbox_service.id, version=11)

        for content_block in inbox_message.content_blocks:

            is_supported = inbox_service.is_content_supported(content_block.content_binding, version=11)

            # FIXME: is it a right thing to do?
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

            inbox_service.server.storage.save_content_block(content_block, inbox_message_entity=inbox_message_entity,
                    collections=supporting_collections, version=11)

            saved_blocks += 1
        

        # Create and return a Status Message indicating success
        status_message = tm11.StatusMessage(
            message_id = generate_message_id(),
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

        inbox_message_entity = inbox_service.server.storage.save_inbox_message(inbox_message, received_via=inbox_service.id, version=10)

        for content_block in inbox_message.content_blocks:
            is_supported = inbox_service.is_content_supported(content_block.content_binding, version=10)

            # FIXME: is it a right thing to do?
            if not is_supported:
                continue

            inbox_service.server.storage.save_content_block(content_block, inbox_message_entity=inbox_message_entity, version=10)


        status_message = tm10.StatusMessage(
            message_id = generate_message_id(),
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
