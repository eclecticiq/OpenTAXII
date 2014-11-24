from .abstract import *

collection_service_to_collections = Table('collection_service_to_collections', Base.metadata,
    Column('service_id', Integer, ForeignKey('collection_management_services.id')),
    Column('collection_id', Integer, ForeignKey('collections.id'))
)
collection_service_to_queries = Table('collection_service_to_queries', Base.metadata,
    Column('service_id', Integer, ForeignKey('collection_management_services.id')),
    Column('query_id', Integer, ForeignKey('supported_queries.id'))
)

class CollectionManagementService(_TaxiiService):
    """
    Model for Collection Management Service. This is also used
    for Feed Management Service.
    """

    __tablename__ = 'collection_management_services'

    service_type = SVC_COLLECTION_MANAGEMENT

#    collection_information_handler = models.ForeignKey('MessageHandler',
#                                                       related_name='collection_information',
#                                                       limit_choices_to={'supported_messages__contains':
#                                                                         'CollectionInformationRequest'},
#                                                       blank=True,
#                                                       null=True)
#    subscription_management_handler = models.ForeignKey('MessageHandler',
#                                                        related_name='subscription_management',
#                                                        limit_choices_to={'supported_messages__contains':
#                                                                          'ManageCollectionSubscriptionRequest'},
#                                                        blank=True,
#                                                        null=True)

    advertised_collections = relationship('DataCollection', secondary=collection_service_to_collections, backref='collection_management_services')
    supported_queries = relationship('SupportedQuery', secondary=collection_service_to_queries, nullable=True)

    def get_message_handler(self, taxii_message):
        mt = taxii_message.message_type
        if mt == MSG_COLLECTION_INFORMATION_REQUEST:
            return self.collection_information_handler
        elif mt == MSG_FEED_INFORMATION_REQUEST:
            return self.collection_information_handler
        elif mt == MSG_MANAGE_COLLECTION_SUBSCRIPTION_REQUEST:
            return self.subscription_management_handler
        elif mt == MSG_MANAGE_FEED_SUBSCRIPTION_REQUEST:
            return self.subscription_management_handler

        return None
        #raise StatusMessageException(taxii_message.message_id, ST_FAILURE, message="Message not supported by this service")




discovery_service_to_discovery_services = Table('discovery_service_to_discovery_services', Base.metadata,
    Column('advertiser_id', Integer, ForeignKey('discovery_services.id')),
    Column('advertised_id', Integer, ForeignKey('discovery_services.id'))
)
discovery_service_to_collection_services = Table('discovery_service_to_collection_services', Base.metadata,
    Column('advertiser_id', Integer, ForeignKey('discovery_services.id')),
    Column('advertised_id', Integer, ForeignKey('collection_management_services.id'))
)

class DiscoveryService(_TaxiiService):
    """
    Model for a TAXII Discovery Service
    """
    service_type = SVC_DISCOVERY

    #discovery_handler = models.ForeignKey('MessageHandler', limit_choices_to={'supported_messages__contains': 'DiscoveryRequest'})

    advertised_discovery_services = relationship(
        'DiscoveryService',
        secondary = advertised_discovery_services,
        backref = 'advertisers',
        primaryjoin = id == discovery_service_to_discovery_services.advertiser_id
    )

    advertised_collection_management_services = relationship(
        'CollectionManagementService',
        secondary = advertised_discovery_services,
        backref = 'advertisers',
        primaryjoin = id == discovery_service_to_discovery_services.advertiser_id
    )

#    advertised_inbox_services = models.ManyToManyField('InboxService', blank=True)
#    advertised_poll_services = models.ManyToManyField('PollService', blank=True)
#    advertised_collection_management_services = models.ManyToManyField('CollectionManagementService', blank=True)

    def get_message_handler(self, taxii_message):
        if taxii_message.message_type == MSG_DISCOVERY_REQUEST:
            return self.discovery_handler

        raise StatusMessageException(taxii_message.message_id, ST_FAILURE, message="Message not supported by this service")

    def get_advertised_services(self):
        """
        Returns:
            A list of DiscoveryService, InboxService, PollService, and
            CollectionManagementService objects that this DiscoveryService
            advertises
        """
        # Chain together all the enabled services that this discovery service advertises
        advertised_services = list(chain(self.advertised_discovery_services.filter(enabled=True),
                                         self.advertised_poll_services.filter(enabled=True),
                                         self.advertised_inbox_services.filter(enabled=True),
                                         self.advertised_collection_management_services.filter(enabled=True)))
        return advertised_services


