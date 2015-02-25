from collections import namedtuple

from .taxii.services import (
        DiscoveryService, InboxService, CollectionManagementService,
        PollService
)
from .utils import get_path_and_address

import structlog
log = structlog.get_logger(__name__)

TYPE_TO_SERVICE = dict(
    inbox = InboxService,
    discovery = DiscoveryService,
    collection_management = CollectionManagementService,
    poll = PollService
)

class TAXIIServer(object):


    def __init__(self, domain, data_manager):

        self.data_manager = data_manager
        self.domain = domain

        self.services = []
        self.path_to_service = dict()

        self._create_services(data_manager.get_services())

        log.info('%d services configured' % len(self.services))


    def _create_services(self, services):

        discovery_services = []

        for _type, id, props in services:

            _props = dict(props)
            _props['server'] = self

            raw_address = _props['address']
            advertised = _props.pop('advertised_services', None)

            path, _props['address'] = get_path_and_address(self.domain, raw_address)

            if _type not in TYPE_TO_SERVICE:
                raise RuntimeError('Unknown service type "%s"' % _type)

            service = TYPE_TO_SERVICE[_type](id=id, **_props)

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

        service_ids = self.data_manager.get_service_ids_for_collection(collection,
                service_type=service_type)
        services = self.get_services(service_ids)

        return services

