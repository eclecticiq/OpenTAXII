# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

from .base_handlers import BaseMessageHandler
from ..exceptions import StatusMessageException

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import *
from libtaxii.common import generate_message_id


class InboxMessage11Handler(BaseMessageHandler):
    """
    Built-in TAXII 1.1 Inbox Message Handler.
    """

    supported_request_messages = [tm11.InboxMessage]
    version = "1"

    @classmethod
    def save_content_block(cls, content_block, supporting_collections):
        """
        Saves the content_block in the database and
        associates it with all DataCollections in supporting_collections.

        This can be overriden to save the content block in a custom way.

        Arguments:
            content_block (tm11.ContentBlock) - The content block to save
            supporting_collections (list of models.DataCollection) - The Data Collections to add this content_block to
        """
        # TODO: Could/should this take an InboxService model object?
        cb = models.ContentBlock.from_content_block_11(content_block)
        cb.save()

        for collection in supporting_collections:
            collection.content_blocks.add(cb)

    @classmethod
    def handle_message(cls, inbox_service, inbox_message, django_request):
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

        collections = inbox_service.validate_destination_collection_names(inbox_message.destination_collection_names,
                                                                          inbox_message.message_id)

        # Store certain information about this Inbox Message in the database for bookkeeping
        inbox_message_db = models.InboxMessage.from_inbox_message_11(inbox_message,
                                                                     django_request,
                                                                     received_via=inbox_service)
        inbox_message_db.save()

        # Iterate over the ContentBlocks in the InboxMessage and try to add
        # them to the database
        saved_blocks = 0
        for content_block in inbox_message.content_blocks:
            # 3a. Identify whether the InboxService supports the Content Block's Content Binding
            # TODO: Is this useful?
            inbox_support_info = inbox_service.is_content_supported(content_block.content_binding)

            supporting_collections = []
            for collection in collections:
                collection_support_info = collection.is_content_supported(content_block.content_binding)
                if collection_support_info.is_supported:
                    supporting_collections.append(collection)

            if len(supporting_collections) == 0 and not inbox_support_info.is_supported:
                # There's nothing to add this content block to
                continue

            cls.save_content_block(content_block, supporting_collections)

            saved_blocks += 1

        # Update the Inbox Message model with the number of ContentBlocks that were saved
        inbox_message_db.content_blocks_saved = saved_blocks
        inbox_message_db.save()

        # Create and return a Status Message indicating success
        status_message = tm11.StatusMessage(message_id=generate_message_id(),
                                            in_response_to=inbox_message.message_id,
                                            status_type=ST_SUCCESS)
        return status_message


class InboxMessage10Handler(BaseMessageHandler):
    """
    Built in TAXII 1.0 Message Handler
    """
    supported_request_messages = [tm10.InboxMessage]
    version = "1"

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
    version = "1"

    @staticmethod
    def handle_message(inbox_service, inbox_message, django_request):
        """
        Passes the request to either InboxMessage10Handler or InboxMessage11Handler
        """
        if isinstance(inbox_message, tm10.InboxMessage):
            return InboxMessage10Handler.handle_message(inbox_service, inbox_message, django_request)
        elif isinstance(inbox_message, tm11.InboxMessage):
            return InboxMessage11Handler.handle_message(inbox_service, inbox_message, django_request)
        else:
            raise StatusMessageException(inbox_message.message_id,
                                         ST_FAILURE,
                                         "TAXII Message not supported by Message Handler.")
