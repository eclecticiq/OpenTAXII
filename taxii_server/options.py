import os
import sys
import anyconfig

from .utils import SimpleRenderer

import structlog
log = structlog.get_logger(__name__)

current_dir = os.path.dirname(os.path.realpath(__file__))

CONFIG_ENV_VAR = 'TAXII_SERVER_CONFIG'
DEFAULT_CONFIG = os.path.join(current_dir, 'defaults.yml')


class ServerConfig(dict):

    def __init__(self, server_properties=None, services_properties=None,
            default_config_file=DEFAULT_CONFIG, optional_env_var=CONFIG_ENV_VAR):

        config_paths = [default_config_file]

        env_var_path = os.environ.get(optional_env_var)
        if env_var_path:
            config_paths.append(env_var_path)

        options = anyconfig.load(config_paths, forced_type="yaml", ignore_missing=False)

        self.update(options)

        if server_properties:
            self['server'].update(server_properties)
        if services_properties:
            self['services'].update(services_properties)


    @property
    def services(self):

        defaults = self['services_defaults']

        services = []

        for _id, props in self['services'].items():

            _props = dict(props)
            _type = _props.pop('type')

            options = dict(defaults[_type])
            options.update(_props)
            
            services.append((_type, _id, options))

        return services

