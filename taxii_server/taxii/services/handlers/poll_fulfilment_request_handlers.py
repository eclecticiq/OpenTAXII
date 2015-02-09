
from .base_handlers import BaseMessageHandler
from ..exceptions import StatusMessageException

import libtaxii.messages_11 as tm11
from libtaxii.constants import *


class PollFulfillmentRequest11Handler(BaseMessageHandler):
    """
    Built-in TAXII 1.1 Poll Fulfillment Request Handler.
    """
    supported_request_messages = [tm11.PollFulfillmentRequest]
    version = "1"

    @staticmethod
    def handle_message(poll_service, poll_fulfillment_request, django_request):
        """
        Looks in the database for a matching result set part and return it.

        Workflow:
            1. Look in models.ResultSetPart for a ResultSetPart that matches the criteria of the request
            2. Update the ResultSetPart's parent (models.ResultSet) to store which ResultSetPart was most recently returned
            3. Turn the ResultSetPart into a PollResponse, and return it
        """
        try:
            rsp = models.ResultSetPart.objects.get(result_set__pk=poll_fulfillment_request.result_id,
                                                   part_number=poll_fulfillment_request.result_part_number,
                                                   result_set__data_collection__name=poll_fulfillment_request.collection_name)

            poll_response = rsp.to_poll_response_11(poll_fulfillment_request.message_id)
            rsp.result_set.last_part_returned = rsp
            rsp.save()
            return poll_response
        except models.ResultSetPart.DoesNotExist:
            raise StatusMessageException(poll_fulfillment_request.message_id,
                                         ST_NOT_FOUND,
                                         {SD_ITEM: str(poll_fulfillment_request.result_id)})

# PollFulfillment is new in TAXII 1.1, so there aren't any TAXII 1.0 handlers for it


class PollFulfillmentRequestHandler(BaseMessageHandler):
    """
    Built-in TAXII 1.1 and TAXII 1.0 Poll Request Handler
    """

    supported_request_messages = [tm11.PollFulfillmentRequest]
    version = "1"

    @staticmethod
    def handle_message(poll_service, poll_fulfillment_request, django_request):
        if isinstance(poll_fulfillment_request, tm11.PollFulfillmentRequest):
            return PollFulfillmentRequest11Handler.handle_message(poll_service, poll_fulfillment_request, django_request)
        else:
            raise StatusMessageException(poll_fulfillment_request.message_id,
                                         ST_FAILURE,
                                         "TAXII Message not supported by Message Handler.")



