import structlog
import importlib

from .taxii.services import (
        DiscoveryService, InboxService, CollectionManagementService,
        PollService
)
from .persistence import PersistenceManager
from .auth import AuthManager
from .utils import get_path_and_address, load_api

log = structlog.get_logger(__name__)


class TAXIIServer(object):
    '''TAXII Server class.
    
    This class keeps Presistence API and Auth API managers instances
    and creates TAXII Service instances on request.

    This class can be initiated directly but should be created via
    :py:func:`create_server`.

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

    def __init__(self, config):

        persistence_api = load_api(config['persistence_api'])
        log.info("api.persistence.loaded",
                 api_class=persistence_api.__class__.__name__)
        self.persistence = PersistenceManager(api=persistence_api)

        auth_api = load_api(config['auth_api'])
        log.info("api.auth.loaded", api_class=auth_api.__class__.__name__)
        self.auth = AuthManager(api=auth_api)

        self.config = config

        signal_hooks = config['hooks']
        if signal_hooks:
            importlib.import_module(signal_hooks)
            log.info("signal_hooks.imported", hooks=signal_hooks)

        log.info("taxiiserver.configured")

    def get_domain(self, service_id):
        dynamic = self.persistence.get_domain(service_id)
        return dynamic or self.config.get('domain')

    def _create_services(self, service_entities):

        discovery_services = []
        services = []

        for entity in service_entities:

            _props = dict(entity.properties)
            _props['server'] = self

            _props['path'], _props['address'] = get_path_and_address(
                    self.get_domain(entity.id), _props['address'])

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

    def get_services(self, service_ids=None):
        '''Get services registered with this TAXII server instance.

        :param list service_ids: list of service IDs (as strings)

        :return: list of services
        :rtype: list of :py:class:`opentaxii.taxii.services.abstract.TAXIIService`
        '''

        if service_ids is not None and len(service_ids) == 0:
            return []

        service_entities = self.persistence.get_services()

        # Services needs to be created all at once to ensure that
        # discovery services list all active advertised services
        services = self._create_services(service_entities)

        if service_ids:
            services = filter(lambda s: s.id in service_ids, services)

        return services

    def get_service(self, id):
        '''Get service by ID.

        :param str id: service ID

        :return: service with specified ID or None
        :rtype: :py:class:`opentaxii.taxii.services.abstract.TAXIIService`
        '''
        
        return next(iter(self.get_services([id])), None)

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

        for_collection = (self.persistence
                              .get_services_for_collection(collection))

        ids_for_type = [e.id for e in for_collection if e.type == service_type]

        # Sync services for collection with registered services for this server
        return self.get_services(ids_for_type)
