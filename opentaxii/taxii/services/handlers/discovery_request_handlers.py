
from .base_handlers import BaseMessageHandler
from ...exceptions import raise_failure

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10


class DiscoveryRequest11Handler(BaseMessageHandler):

    supported_request_messages = [tm11.DiscoveryRequest]

    @classmethod
    def handle_message(cls, service, request):

        response = tm11.DiscoveryResponse(
            cls.generate_id(), request.message_id)
        for service in service.advertised_services:
            service_instances = service.to_service_instances(version=11)
            response.service_instances.extend(service_instances)

        return response


class DiscoveryRequest10Handler(BaseMessageHandler):

    supported_request_messages = [tm10.DiscoveryRequest]

    @classmethod
    def handle_message(cls, service, request):

        response = tm10.DiscoveryResponse(
            cls.generate_id(), request.message_id)

        for service in service.advertised_services:
            service_instances = service.to_service_instances(version=10)
            response.service_instances.extend(service_instances)

        return response


class DiscoveryRequestHandler(BaseMessageHandler):

    supported_request_messages = [tm10.DiscoveryRequest, tm11.DiscoveryRequest]

    @classmethod
    def handle_message(cls, service, request):

        if isinstance(request, tm10.DiscoveryRequest):
            return DiscoveryRequest10Handler.handle_message(service, request)
        elif isinstance(request, tm11.DiscoveryRequest):
            return DiscoveryRequest11Handler.handle_message(service, request)
        else:
            raise_failure("TAXII Message not supported by message handler",
                          request.message_id)
