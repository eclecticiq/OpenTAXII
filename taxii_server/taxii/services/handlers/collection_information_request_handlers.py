
from .base_handlers import BaseMessageHandler

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.common import generate_message_id


class CollectionInformationRequest11Handler(BaseMessageHandler):

    supported_request_messages = [tm11.CollectionInformationRequest]

    @staticmethod
    def handle_message(collection_management_service, collection_information_request):

        in_response_to = collection_information_request.message_id

        return collection_management_response(collection_management_service,
                in_response_to, version=11)


class FeedInformationRequest10Handler(BaseMessageHandler):

    supported_request_messages = [tm10.FeedInformationRequest]

    @staticmethod
    def handle_message(collection_management_service, feed_information_request):

        in_response_to = feed_information_request.message_id

        return collection_management_response(collection_management_service,
                in_response_to, version=10)


class CollectionInformationRequestHandler(BaseMessageHandler):

    supported_request_messages = [tm10.FeedInformationRequest, tm11.CollectionInformationRequest]

    @staticmethod
    def handle_message(collection_management_service, collection_information_request):

        cms = collection_management_service
        cir = collection_information_request

        if isinstance(collection_information_request, tm10.FeedInformationRequest):
            return FeedInformationRequest10Handler.handle_message(cms, cir)
        elif isinstance(collection_information_request, tm11.CollectionInformationRequest):
            return CollectionInformationRequest11Handler.handle_message(cms, cir)
        else:
            raise_failure("TAXII Message not supported by message handler", discovery_request.message_id)


def collection_management_response(service, in_response_to, version):

    if version == 10:
        response = tm10.FeedInformationResponse(message_id=generate_message_id(),
                in_response_to=in_response_to)

        for collection in service.advertised_collections:
            feed = collection_to_feed_information(service, collection)
            response.feed_informations.append(feed)

    else:
        response = tm11.CollectionInformationResponse(message_id=generate_message_id(),
                in_response_to=in_response_to)

        for collection in service.advertised_collections:
            coll = collection_to_collection_information(service, collection)
            response.collection_informations.append(coll)

    return response


def collection_to_feed_information(service, coll):
    return tm10.FeedInformation(
        feed_name = coll.name,
        feed_description = coll.description,
        supported_contents = coll.get_supported_content(version=10),
        available = coll.available,

        push_methods = service.get_push_methods(coll, version=10),
        polling_service_instances = service.get_polling_service_instances(coll, version=10),
        subscription_methods = service.get_subscription_methods(coll, version=10),
        # collection_volume, collection_type, and receiving_inbox_services are not supported in TAXII 1.0
    )

def collection_to_collection_information(service, coll):

    inboxe_instances = []

    for inbox in service.get_receiving_inbox_services(coll):
        inboxe_instances.extend(inbox_to_receiving_inbox_instance(inbox))

    return tm11.CollectionInformation(
        collection_name = coll.name,
        collection_description = coll.description,
        supported_contents = coll.get_supported_content(version=11),
        available = coll.available,

        push_methods = service.get_push_methods(coll, version=11),
        polling_service_instances = service.get_polling_service_instances(coll, version=11),
        subscription_methods = service.get_subscription_methods(coll, version=11),

        collection_volume = service.get_volume(coll),
        collection_type = coll.type,
        receiving_inbox_services = inboxe_instances
    )


def inbox_to_receiving_inbox_instance(inbox):
    inbox_instances = []

    for protocol_binding in inbox.supported_protocol_bindings:

        inbox_instances.append(tm11.ReceivingInboxService(
            inbox_protocol = protocol_binding,
            inbox_address = inbox.absolute_address(protocol_binding),
            inbox_message_bindings = inbox.supported_message_bindings,
            supported_contents = inbox.get_supported_content(version=11)
        ))

    return inbox_instances



