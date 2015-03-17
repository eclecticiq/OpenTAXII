import structlog
from collections import namedtuple
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

        self.services = []
        self.path_to_service = dict()

        self.reload_services()


    def reload_services(self):
        self.services = []
        self.path_to_service = dict()
        self._create_services(self.persistence.get_services())

        log.info('services configured', services_count=len(self.services))


    def _create_services(self, services):

        discovery_services = []

        for service in services:

            _props = dict(service.properties)
            _props['server'] = self

            raw_address = _props['address']
            advertised = _props.pop('advertised_services', None)

            path, _props['address'] = get_path_and_address(self.domain, raw_address)

            if service.type not in TYPE_TO_SERVICE:
                raise RuntimeError('Unknown service type "%s"' % service.type)

            service = TYPE_TO_SERVICE[service.type](id=service.id, **_props)

            self.services.append(service)

            if advertised:
                discovery_services.append((service, advertised))

            if path:
                self.path_to_service[path] = service

        for service, advertised in discovery_services:
            service.set_advertised_services([s for s in self.services if s.id in advertised])


    def get_services(self, ids):
        return filter(lambda s: s.id in ids, self.services)


    def get_services_for_collection(self, collection, service_type):

        if not service_type in TYPE_TO_SERVICE:
            raise ValueError('Wrong service type')

        service_entities = self.persistence.get_services_for_collection(collection,
                service_type=service_type)
        services = self.get_services([e.id for e in service_entities])

        return services


def create_server(config=None):

    config = config or ServerConfig()
    attach_signal_hooks(config)

    persistence_api = load_api(config['server']['persistence_api'])
    persistence_manager = PersistenceManager(api=persistence_api)

    auth_api = load_api(config['server']['auth_api'])
    auth_manager = AuthManager(api=auth_api)

    domain = config['server']['domain']
    server = TAXIIServer(domain, persistence_manager=persistence_manager,
            auth_manager=auth_manager)

    return server

