# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

from .base_handlers import BaseMessageHandler
from ..exceptions import StatusMessageException, raise_failure

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import *
from libtaxii.common import generate_message_id

from persistence import *

class InboxMessage11Handler(BaseMessageHandler):
    """
    Built-in TAXII 1.1 Inbox Message Handler.
    """

    supported_request_messages = [tm11.InboxMessage]

    @classmethod
    def save_content_block(cls, content_block, supporting_collections):
        # TODO: Could/should this take an InboxService model object?

        content_block_entity = ContentBlockEntity.from_content_block(content_block, version=11)

        for collection in supporting_collections:
            collection.add_content_block(content_block_entity)

    @classmethod
    def handle_message(cls, inbox_service, inbox_message):
        """
        Attempts to save all Content Blocks in the Inbox Message into the
        database.

        Workflow:
            #. Validate the request's Destination Collection Names against the InboxService model
            #. Create an InboxMessage model object for bookkeeping
            #. Iterate over each Content Block in the request:

             #. Identify which of the request's destination collections support the Content Block's Content Binding
             #. Call `save_content_block(tm11.ContentBlock, <list of Data Collections from 3a>)`

            #. Return Status Message with a Status Type of Success

        Raises:
            A StatusMessageException for errors
        """

        collections = inbox_service.validate_destination_collection_names(
                inbox_message.destination_collection_names, inbox_message.message_id)


        if not collections:
            # FIXME: what are we doing here?
            return

        # Iterate over the ContentBlocks in the InboxMessage and try to add them to the database
        blocks = []

        saved_blocks = 0

        for content_block in inbox_message.content_blocks:
            # 3a. Identify whether the InboxService supports the Content Block's Content Binding
            print content_block
            is_supported = inbox_service.is_content_supported(content_block.content_binding)

            # FIXME: is it a right thing to do?
            if not is_supported:
                continue

            supporting_collections = []
            for collection in collections:
                supported_by_collection = collection.is_content_supported(content_block.content_binding)
                if supported_by_collection:
                    supporting_collections.append(collection)

            if len(supporting_collections) == 0 and not inbox_support_info.is_supported:
                # There's nothing to add this content block to
                continue

            cls.save_content_block(content_block, supporting_collections)

            saved_blocks += 1

        inbox_message_entity = InboxMessageEntity.from_inbox_message(inbox_message, received_via='HEHE', version=11)
        inbox_message_entity.content_blocks_saved = saved_blocks
        inbox_message_entity.save()

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
    def save_content_block(cls, content_block):
        """
        A hook for allowing an override of the saving functionality.
        """
        cb = models.ContentBlock.from_content_block_10(content_block)
        cb.save()

    @classmethod
    def handle_message(cls, inbox_service, inbox_message, django_request):
        """
        """

        collections = inbox_service.validate_destination_collection_names(None,  # Inbox 1.0 doesn't have a DCN
                                                                          inbox_message.message_id)

        # Store certain information about this Inbox Message in the database for bookkeeping
        inbox_message_db = models.InboxMessage.from_inbox_message_10(inbox_message,
                                                                     django_request,
                                                                     received_via=inbox_service)
        inbox_message_db.save()

        saved_blocks = 0
        for content_block in inbox_message.content_blocks:
            inbox_support_info = inbox_service.is_content_supported(content_block.content_binding)
            if inbox_support_info.is_supported is False:
                continue

            cls.save_content_block(content_block)
            saved_blocks += 1

        # Update the Inbox Message model with the number of ContentBlocks that were saved
        inbox_message_db.content_blocks_saved = saved_blocks
        inbox_message_db.save()

        # Create and return a Status Message indicating success
        status_message = tm11.StatusMessage(message_id=generate_message_id(),
                                            in_response_to=inbox_message.message_id,
                                            status_type=ST_SUCCESS)
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
