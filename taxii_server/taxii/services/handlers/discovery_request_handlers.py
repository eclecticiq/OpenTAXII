
from .base_handlers import BaseMessageHandler
from ...exceptions import raise_failure

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.common import generate_message_id


class DiscoveryRequest11Handler(BaseMessageHandler):

    supported_request_messages = [tm11.DiscoveryRequest]

    @staticmethod
    def handle_message(discovery_service, discovery_request):

        response = discovery_service.advertised_services

        return convert_discovery_response(response, discovery_request.message_id, version=11)


class DiscoveryRequest10Handler(BaseMessageHandler):

    supported_request_messages = [tm10.DiscoveryRequest]

    @staticmethod
    def handle_message(discovery_service, discovery_request):

        response = discovery_service.advertised_services

        return convert_discovery_response(response, discovery_request.message_id, version=10)


class DiscoveryRequestHandler(BaseMessageHandler):

    supported_request_messages = [tm10.DiscoveryRequest, tm11.DiscoveryRequest]

    @staticmethod
    def handle_message(discovery_service, discovery_request):

        if isinstance(discovery_request, tm10.DiscoveryRequest):
            return DiscoveryRequest10Handler.handle_message(discovery_service, discovery_request)
        elif isinstance(discovery_request, tm11.DiscoveryRequest):
            return DiscoveryRequest11Handler.handle_message(discovery_service, discovery_request)
        else:
            raise_failure("TAXII Message not supported by message handler", discovery_request.message_id)


def convert_discovery_response(response, in_response_to, version):

    if version == 10:
        discovery_response = tm10.DiscoveryResponse(generate_message_id(), in_response_to)
    else:
        discovery_response = tm11.DiscoveryResponse(generate_message_id(), in_response_to)

    for service in response:
        service_instances = service.to_service_instances(version=version)
        discovery_response.service_instances.extend(service_instances)

    return discovery_response

