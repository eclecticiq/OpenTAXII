
from .base_handlers import BaseMessageHandler

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10

from opentaxii.taxii.exceptions import raise_failure

from ...converters import (
    collection_to_feedcollection_information
)


class CollectionInformationRequest11Handler(BaseMessageHandler):

    supported_request_messages = [tm11.CollectionInformationRequest]

    @classmethod
    def handle_message(cls, service, request):

        response = tm11.CollectionInformationResponse(
            message_id=cls.generate_id(), in_response_to=request.message_id)

        for collection in service.advertised_collections:
            coll = collection_to_feedcollection_information(
                service, collection, version=11)
            response.collection_informations.append(coll)

        return response


class FeedInformationRequest10Handler(BaseMessageHandler):

    supported_request_messages = [tm10.FeedInformationRequest]

    @classmethod
    def handle_message(cls, service, request):

        response = tm10.FeedInformationResponse(
            message_id=cls.generate_id(),
            in_response_to=request.message_id)

        for collection in service.advertised_collections:
            feed = collection_to_feedcollection_information(
                service, collection, version=10)
            response.feed_informations.append(feed)

        return response


class CollectionInformationRequestHandler(BaseMessageHandler):

    supported_request_messages = [
        tm10.FeedInformationRequest, tm11.CollectionInformationRequest]

    @classmethod
    def handle_message(cls, service, request):

        if isinstance(request, tm10.FeedInformationRequest):
            return FeedInformationRequest10Handler.handle_message(
                service, request)
        elif isinstance(request, tm11.CollectionInformationRequest):
            return CollectionInformationRequest11Handler.handle_message(
                service, request)
        else:
            raise_failure(
                "TAXII Message not supported by message handler",
                request.message_id)
