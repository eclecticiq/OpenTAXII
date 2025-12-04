from libtaxii.constants import MSG_DISCOVERY_REQUEST, SVC_DISCOVERY

from .abstract import TAXIIService
from .handlers import DiscoveryRequestHandler


class DiscoveryService(TAXIIService):

    service_type = SVC_DISCOVERY

    handlers = {MSG_DISCOVERY_REQUEST: DiscoveryRequestHandler}

    advertised_services = []

    def __init__(self, services=None, **kwargs):
        super(DiscoveryService, self).__init__(**kwargs)
        self.advertised_services = services or []

    def set_advertised_services(self, services):
        self.advertised_services = services
