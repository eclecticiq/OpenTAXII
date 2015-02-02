from libtaxii.constants import (
        SVC_COLLECTION_MANAGEMENT,
        MSG_COLLECTION_INFORMATION_REQUEST, MSG_FEED_INFORMATION_REQUEST,
        MSG_MANAGE_COLLECTION_SUBSCRIPTION_REQUEST, MSG_MANAGE_FEED_SUBSCRIPTION_REQUEST
)

from .abstract import TaxiiService
from .handlers import (
        CollectionInformationRequestHandler, CollectionInformationRequestHandler,
        SubscriptionRequestHandler, SubscriptionRequestHandler
)


class CollectionManagementService(TaxiiService):

    handlers = {
        MSG_COLLECTION_INFORMATION_REQUEST : CollectionInformationRequestHandler,
        MSG_FEED_INFORMATION_REQUEST : CollectionInformationRequestHandler,

        MSG_MANAGE_COLLECTION_SUBSCRIPTION_REQUEST : SubscriptionRequestHandler,
        MSG_MANAGE_FEED_SUBSCRIPTION_REQUEST : SubscriptionRequestHandler
    }
            
    service_type = SVC_COLLECTION_MANAGEMENT

    supported_queries = []

    def __init__(self, advertised_services=[], **kwargs):
        super(DiscoveryService, self).__init__(**kwargs)

        self.advertised_services = advertised_services

    def get_advertised_collections(self):
        return []



