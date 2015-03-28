import structlog

from .taxii.services import (
        DiscoveryService, InboxService, CollectionManagementService,
        PollService
)
from .config import ServerConfig
from .persistence import PersistenceManager
from .auth import AuthManager
from .utils import get_path_and_address, attach_signal_hooks, load_api

log = structlog.get_logger(__name__)

class TAXIIServer(object):
    '''TAXII Server class.
    
    This class keeps Presistence API and Auth API managers instances
    and creates TAXII Service instances on request.

    This class can be initiated directly but should be created via
    :py:func:`create_server`.

    :param str domain: domain name that will be used in
                       services absolute address values
    :param `opentaxii.persistence.manager.PersistenceManager` persistence_manager:
                       persistence manager instance
    :param `opentaxii.auth.manager.AuthManager` auth_manager:
                       authentication manager instance
    '''

    TYPE_TO_SERVICE = dict(
        inbox = InboxService,
        discovery = DiscoveryService,
        collection_management = CollectionManagementService,
        poll = PollService
    )

    def __init__(self, domain, persistence_manager, auth_manager):

        self.domain = domain

        self.persistence = persistence_manager
        self.auth = auth_manager


    def _create_services(self, service_entities):

        discovery_services = []
        services = []

        for entity in service_entities:

            _props = dict(entity.properties)
            _props['server'] = self

            _props['path'], _props['address'] = get_path_and_address(
                    self.domain, _props['address'])

            advertised = _props.pop('advertised_services', None)

            if entity.type not in self.TYPE_TO_SERVICE:
                raise ValueError('Unknown service type "%s"' % entity.type)

            service = self.TYPE_TO_SERVICE[entity.type](id=entity.id, **_props)

            services.append(service)

            if advertised:
                discovery_services.append((service, advertised))

        for service, advertised in discovery_services:
            service.set_advertised_services([s for s in services if s.id in advertised])

        return services

    def get_services(self, ids=None):
        '''Get services registered with this TAXII server instance.

        :param list ids: list of service IDs (as strings) to use as a filter

        :return: list of services
        :rtype: list of :py:class:`opentaxii.taxii.services.abstract.TAXIIService`
        '''

        if ids is not None and len(ids) == 0:
            return []

        service_entities = self.persistence.get_services()
        # Services needs to be created all at once to ensure that
        # discovery services list all active advertised services
        services = self._create_services(service_entities)

        if ids:
            services = filter(lambda s: s.id in ids, services)

        return services

    def get_service(self, id):
        '''Get service by ID.

        :param str id: service ID

        :return: service with specified ID or None
        :rtype: :py:class:`opentaxii.taxii.services.abstract.TAXIIService`
        '''
        
        services = self.get_services([id])
        if services:
            return services[0]

    def get_services_for_collection(self, collection, service_type):
        '''Get list of services with type ``service_type``, attached
        to collection ``collection``.

        :param `opentaxii.taxii.entities.CollectionEntity` collection:
                    collection in question
        :param str service_type: service type, supported values are
                    listed as keys in :py:attr:`TYPE_TO_SERVICE`

        :return: list of services
        :rtype: list of :py:class:`opentaxii.taxii.services.abstract.TAXIIService`
        '''

        if service_type not in self.TYPE_TO_SERVICE:
            raise ValueError('Wrong service type: %s' % service_type)

        entities = self.persistence.get_services_for_collection(collection)

        requested_entities = [e.id for e in entities if e.type == service_type]

        if not requested_entities:
            return []

        # Sync services for collection with registered services for this server
        services = self.get_services(requested_entities)

        return services


def create_server(config=None):
    '''Create TAXII server instance.

    Function gets required parameters from the config (domain name,
    API class names, hooks module name), creates API instances and configures
    new TAXII server instance.

    :param `opentaxii.config.ServerConfig` config: config instance

    :return: TAXII server instance
    :rtype: :py:class:`opentaxii.server.TAXIIServer`
    '''

    config = config or ServerConfig()
    attach_signal_hooks(config)

    persistence_api = load_api(config['persistence_api'])
    persistence_manager = PersistenceManager(api=persistence_api)

    auth_api = load_api(config['auth_api'])
    auth_manager = AuthManager(api=auth_api)

    domain = config['domain']
    server = TAXIIServer(domain, persistence_manager=persistence_manager,
            auth_manager=auth_manager)

    return server

