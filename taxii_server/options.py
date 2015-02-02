import os
import sys
import ConfigParser

from functools import partial

from .taxii.bindings import ContentBinding
from .utils import SimpleRenderer

import structlog
log = structlog.get_logger(__name__)

current_dir = os.path.dirname(os.path.realpath(__file__))
CONFIG_ENV_VAR = 'TAXII_SERVER_CONFIG'
DEFAULT_CONFIG = os.path.join(current_dir, 'default_config.ini')


SECTION_OPTIONS = dict(
    server = dict(
        defaults = 'server',
        booleans = ['create_tables'],
        lists = []
    ),
    inbox = dict(
        defaults = 'defaults:inbox',
        booleans = ['accept_all_content', 'destination_collection_required'],
        lists = ['supported_content', 'protocol_bindings']
    ),
    discovery = dict(
        defaults = 'defaults:discovery',
        booleans = [],
        lists = ['advertised_services', 'protocol_bindings']
    )
)



class ServerConfig(ConfigParser.RawConfigParser, object):

    def __init__(self, *args, **kwargs):
        super(ServerConfig, self).__init__(*args, **kwargs)

        server_options_getter = partial(getter, self, 'server', **SECTION_OPTIONS['server'])
        self.server = SectionProxy(server_options_getter)


    @property
    def unpacked_services(self):
        services = []
        for section in self.sections():

            if not section.startswith('service:'):
                continue

            type, id = section.replace('service:', '').split(':')
            options = self.get_options(type, section)
            
            services.append((type, id, options))

        return services


    def get_options(self, type, section):

        if type not in SECTION_OPTIONS:
            raise RuntimeError('Unknown service type "%s"' % type)

        section_options = SECTION_OPTIONS[type]

        defaults_section = section_options['defaults']
        booleans = section_options['booleans']
        lists = section_options['lists']

        options = dict()
        options = self.__populate_with_options(options, defaults_section, booleans=booleans, lists=lists)
        options = self.__populate_with_options(options, section, booleans=booleans, lists=lists)

        return options


    def __populate_with_options(self, dest, section, booleans=[], lists=[]):

        for option in self.options(section):
            if option in booleans:
                dest[option] = self.getboolean(section, option)
            elif option in lists:
                dest[option] = _string_list(self.get(section, option))
            else:
                dest[option] = self.get(section, option)

        return dest

    @staticmethod
    def load(server_properties=None, services_properties=[], base_config=DEFAULT_CONFIG, optional_env_var=CONFIG_ENV_VAR):

        config = ServerConfig()

        with open(base_config, 'r') as f:
            config.readfp(f)

        log.info('Loaded basic config from %s' % base_config)

        env_var_conf = os.environ.get(optional_env_var)

        if env_var_conf:
            if not config.read(env_var_conf):
                raise RuntimeError('Can not load configuration from the path configured in the '
                        'environment variable: %s = %s' % (optional_env_var, env_var_conf))
            else:
                log.info('Loaded a config from %s' % env_var_conf)

        if server_properties:
            config.server_config_from_obj(server_properties)

        if services_properties:
            config.services_config_from_obj(services_properties)

        return config


    def server_config_from_obj(self, config):
        for option, value in config.items():
            self.set('server', option, value)


    def services_config_from_obj(self, services):
        for service in services:

            options = dict((key, value) for key, value in service.items() if key not in ['type', 'id'])

            section = 'service:%s:%s' % (service['type'], service['id'])
            self.add_section(section)
            for option, value in options.items():
                self.set(section, option, value)



def getter(config, section, key, booleans=[], lists=[], defaults=None):
    if key in booleans:
        return config.getboolean(section, key)
    elif key in lists:
        return _string_list(config.get(section, key))
    else:
        return config.get(section, key)



class SectionProxy(object):

    def __init__(self, getter):
        self.get = getter

    def __getattr__(self, key):
        return self.get(key)
        

def _string_list(s):
    if not s:
        return []
    elif isinstance(s, list):
        return s

    return map(lambda x: x.strip(), s.split(','))


