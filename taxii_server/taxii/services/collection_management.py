from libtaxii.constants import (
        SVC_COLLECTION_MANAGEMENT,
        MSG_COLLECTION_INFORMATION_REQUEST, MSG_FEED_INFORMATION_REQUEST,
        MSG_MANAGE_COLLECTION_SUBSCRIPTION_REQUEST, MSG_MANAGE_FEED_SUBSCRIPTION_REQUEST,
)

from .abstract import TaxiiService
from .handlers import (
        CollectionInformationRequestHandler,
        #SubscriptionRequestHandler
)


class CollectionManagementService(TaxiiService):

    handlers = {
        MSG_COLLECTION_INFORMATION_REQUEST : CollectionInformationRequestHandler,
        MSG_FEED_INFORMATION_REQUEST : CollectionInformationRequestHandler,

#        MSG_MANAGE_COLLECTION_SUBSCRIPTION_REQUEST : SubscriptionRequestHandler,
#        MSG_MANAGE_FEED_SUBSCRIPTION_REQUEST : SubscriptionRequestHandler
    }
            
    service_type = SVC_COLLECTION_MANAGEMENT

    def __init__(self, **kwargs):
        super(CollectionManagementService, self).__init__(**kwargs)

    @property
    def advertised_collections(self):
        return self.server.data_manager.get_collections(service_id=self.id)


    def get_push_methods(self, collection, version):
        # Push delivery is not implemented
        pass

    def get_polling_service_instances(self, collection, version):
        pass

    def get_subscription_methods(self, collection, version):
        # Subscription service is not implemented
        pass

    def get_receiving_inbox_services(self, collection):
        service_ids = self.server.data_manager.get_service_ids_for_collection(collection,
                service_type='inbox')
        services = self.server.get_services(service_ids)

        return services

    def get_volume(self, collection):
        return 10


