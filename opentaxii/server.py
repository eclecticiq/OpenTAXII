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

TYPE_TO_SERVICE = dict(
    inbox = InboxService,
    discovery = DiscoveryService,
    collection_management = CollectionManagementService,
    poll = PollService
)

class TAXIIServer(object):

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

            if entity.type not in TYPE_TO_SERVICE:
                raise ValueError('Unknown service type "%s"' % entity.type)

            service = TYPE_TO_SERVICE[entity.type](id=entity.id, **_props)

            services.append(service)

            if advertised:
                discovery_services.append((service, advertised))

        for service, advertised in discovery_services:
            service.set_advertised_services([s for s in services if s.id in advertised])

        return services

    def get_services(self, ids=None):
        service_entities = self.persistence.get_services()
        # Services needs to be created all at once to ensure that
        # discovery services list all active advertised services
        services = self._create_services(service_entities)

        if ids:
            services = filter(lambda s: s.id in ids, services)

        return services

    def get_service(self, id):
        services = self.get_services([id])
        if services:
            return services[0]

    def get_services_for_collection(self, collection, service_type):

        if service_type not in TYPE_TO_SERVICE:
            raise ValueError('Wrong service type: %s' % service_type)

        service_entities = self.persistence.get_services_for_collection(
                collection, service_type=service_type)

        # Sync services for collection with registered services for this server
        services = self.get_services([e.id for e in service_entities])

        return services


def create_server(config=None):

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

