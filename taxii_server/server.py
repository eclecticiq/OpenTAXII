from collections import namedtuple

from .taxii.services import DiscoveryService, InboxService
from .utils import get_path_and_address

import structlog
log = structlog.get_logger(__name__)

class TAXIIServer(object):


    def __init__(self, domain, services_properties, storage):

        self.storage = storage 
        self.domain = domain

        self.services = []
        self.path_to_service = dict()

        self.__create_services(services_properties)

        log.info('%d services configured' % len(self.services))


    def __create_services(self, services):

        discovery_services = []

        for type, id, options in services:

            options['server'] = self
            path, options['address'] = get_path_and_address(self.domain, options['address'])

            if type == 'inbox':
                service = InboxService(id=id, **options)
            elif type == 'discovery':
                advertised = options.pop('advertised_services')
                service = DiscoveryService(id=id, **options)

                if advertised:
                    discovery_services.append((service, advertised))
            else:
                raise RuntimeError('Unknown service type "%s"' % type)

            self.services.append(service)

            if path:
                self.path_to_service[path] = service

        for service, advertised in discovery_services:
            service.set_advertised_services([s for s in self.services if s.id in advertised])


