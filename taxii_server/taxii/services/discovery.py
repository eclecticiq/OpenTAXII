from libtaxii.constants import SVC_DISCOVERY, MSG_DISCOVERY_REQUEST

from .abstract import TaxiiService
from .handlers import DiscoveryRequestHandler

class DiscoveryService(TaxiiService):

    service_type = SVC_DISCOVERY

    handlers = {
        MSG_DISCOVERY_REQUEST : DiscoveryRequestHandler
    }

    advertised_services = []

    def __init__(self, services=[], **kwargs):
        super(DiscoveryService, self).__init__(**kwargs)

        self.advertised_services = services


    def set_advertised_services(self, services):
        self.advertised_services = services


