
from .base_handlers import BaseMessageHandler

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10


class CollectionInformationRequest11Handler(BaseMessageHandler):
    """
    Built-in TAXII 1.1 Collection Information Request Handler.
    """
    supported_request_messages = [tm11.CollectionInformationRequest]
    version = "1"

    @staticmethod
    def handle_message(collection_management_service, collection_information_request, django_request):
        """
        Workflow:
            1. Returns the result of `models.CollectionManagementService.to_collection_information_response_11()`
        """
        in_response_to = collection_information_request.message_id
        return collection_management_service.to_collection_information_response_11(in_response_to)


class FeedInformationRequest10Handler(BaseMessageHandler):
    """
    Built-in TAXII 1.0 Feed Information Request Handler
    """
    supported_request_messages = [tm10.FeedInformationRequest]
    version = "1"

    @staticmethod
    def handle_message(collection_management_service, feed_information_request, django_request):
        """
        Workflow:
            1. Returns the result of `models.CollectionManagementService.to_feed_information_response_10()`
        """
        in_response_to = feed_information_request.message_id
        return collection_management_service.to_feed_information_response_10(in_response_to)


class CollectionInformationRequestHandler(BaseMessageHandler):
    """
    Built-in TAXII 1.1 and 1.0 Collection/Feed Information Request handler.
    """

    supported_request_messages = [tm10.FeedInformationRequest, tm11.CollectionInformationRequest]
    version = "1"

    @staticmethod
    def handle_message(collection_management_service, collection_information_request, django_request):
        """
        Passes the request to either FeedInformationRequest10Handler
        or CollectionInformationRequestRequest11Handler.
        """
        # aliases because the names are long
        cms = collection_management_service
        cir = collection_information_request
        dr = django_request

        if isinstance(collection_information_request, tm10.FeedInformationRequest):
            return FeedInformationRequest10Handler.handle_message(cms, cir, dr)
        elif isinstance(collection_information_request, tm11.CollectionInformationRequest):
            return CollectionInformationRequest11Handler.handle_message(cms, cir, dr)
        else:
            raise ValueError("Unsupported message!")
