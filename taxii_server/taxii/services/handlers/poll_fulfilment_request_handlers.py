import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import *
from libtaxii.common import generate_message_id

from .base_handlers import BaseMessageHandler
from ...exceptions import StatusMessageException, raise_failure
from ....data.exceptions import ResultsNotReady

from ...entities import CollectionEntity
from ...transform import to_content_bindings
from ...utils import get_utc_now

from .poll_request_handlers import PollRequest11Handler

class PollFulfilmentRequest11Handler(BaseMessageHandler):

    supported_request_messages = [tm11.PollFulfillmentRequest]

    @staticmethod
    def handle_message(service, request):

        result_id = request.result_id
        part_number = request.result_part_number
        collection_name = request.collection_name

        result_set = service.get_result_set(result_id)

        collection = PollRequest11Handler.get_collection(service, collection_name,
                in_response_to=request.message_id)

        if not result_set or result_set.collection_id != collection.id:
            raise StatusMessageException(ST_NOT_FOUND, in_response_to=request.message_id,
                status_details={SD_ITEM: result_id})
            
        response = PollRequest11Handler.prepare_poll_response(
            service = service,
            collection = collection,
            in_response_to = request.message_id, 
            timeframe = result_set.timeframe,
            content_bindings = result_set.content_bindings,
            result_part = part_number,
            allow_async = True,
            return_content = True,
            result_id = result_id
        )
        return response

# TAXII 1.0 does not support PollFulfillment


class PollFulfilmentRequestHandler(BaseMessageHandler):

    supported_request_messages = [tm11.PollFulfillmentRequest]

    @staticmethod
    def handle_message(service, request):
        if isinstance(request, tm11.PollFulfillmentRequest):
            return PollFulfilmentRequest11Handler.handle_message(service, request)
        else:
            raise_failure("TAXII Message not supported by message handler", request.message_id)



