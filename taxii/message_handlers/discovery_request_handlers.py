# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

from .base_handlers import BaseMessageHandler
from ..exceptions import raise_failure

from ..transform import convert_discovery_response

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10


class DiscoveryRequest11Handler(BaseMessageHandler):

    supported_request_messages = [tm11.DiscoveryRequest]

    @staticmethod
    def handle_message(discovery_service, discovery_request):

        response = discovery_service.get_advertised_services()

        return convert_discovery_response(response, discovery_request.message_id, v=11)


class DiscoveryRequest10Handler(BaseMessageHandler):

    supported_request_messages = [tm10.DiscoveryRequest]

    @staticmethod
    def handle_message(discovery_service, discovery_request):

        response = discovery_service.get_advertised_services()

        return convert_discovery_response(response, discovery_request.message_id, v=10)


class DiscoveryRequestHandler(BaseMessageHandler):

    supported_request_messages = [tm10.DiscoveryRequest, tm11.DiscoveryRequest]

    @staticmethod
    def handle_message(discovery_service, discovery_request):

        if isinstance(discovery_request, tm10.DiscoveryRequest):
            return DiscoveryRequest10Handler.handle_message(discovery_service, discovery_request)
        elif isinstance(discovery_request, tm11.DiscoveryRequest):
            return DiscoveryRequest11Handler.handle_message(discovery_service, discovery_request)
        else:
            raise raise_failure("TAXII Message not supported by Message Handler", discovery_request.message_id)


