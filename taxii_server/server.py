from collections import namedtuple

from .taxii.services import DiscoveryService, InboxService

import logging
log = logging.getLogger(__name__)

class TAXIIServer(object):

    services = []

    path_to_service = dict()

    def __init__(self, config, storage):

        self.storage = storage 

        self.config = config
        self.domain = self.config.domain
        self.__create_services()

        log.info('%d services configured' % len(self.services))


    def __create_services(self):

        ads = []

        for type, id, section in self.config.services:

            address = self.config.get(section, 'address')

            if not address:
                raise RuntimeException('Service address is not specified for service %s' % section)

            if address.startswith('/'):
                path = address
                service_address = self.domain + path
            else:
                path = None
                service_address = address

            if type == 'inbox':
                options = self.config.inbox_options(section)
                options['address'] = service_address
                service = InboxService(id=id, **options)
            elif type == 'discovery':
                options = self.config.discovery_options(section)
                options['address'] = service_address
                advertised = options.pop('advertised_services', [])
                service = DiscoveryService(id=id, **options)
                ads.append((service, advertised))
            else:
                raise RuntimeException('Unknown service type "%s"' % service_type)

            service.server = self

            if path:
                self.path_to_service[path] = service

            self.services.append(service)

        for service, advertised in ads:
            service.advertised_services = [s for s in self.services if s.id in advertised]

