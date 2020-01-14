import os
from collections import defaultdict

import yaml
from libtaxii.constants import ST_TYPES_10, ST_TYPES_11


current_dir = os.path.dirname(os.path.realpath(__file__))

ENV_VAR_PREFIX = 'OPENTAXII_'
CONFIG_ENV_VAR = 'OPENTAXII_CONFIG'
DEFAULT_CONFIG_NAME = 'defaults.yml'
DEFAULT_CONFIG = os.path.join(current_dir, DEFAULT_CONFIG_NAME)


def _infinite_dict():
    return defaultdict(_infinite_dict)


class ServerConfig(dict):
    '''Class responsible for loading configuration files.

    This class will load default configuration file (shipped with OpenTAXII)
    and apply user specified configuration file on top of default one.

    Users can specify custom configuration file (YAML formatted) using
    enviromental variable. The variable should contain a full path to
    a custom configuration file.

    :param str optional_env_var: name of the enviromental variable
    :param list extra_configs: list of additional config filenames
    '''

    def __init__(self, optional_env_var=CONFIG_ENV_VAR, extra_configs=None):

        configs = [DEFAULT_CONFIG]
        configs.extend(extra_configs or [])
        configs.append(self._get_env_config())

        env_var_path = os.environ.get(optional_env_var)
        if env_var_path:
            configs.append(env_var_path)

        options = self._load_configs(*configs)
        if options['unauthorized_status'] not in ST_TYPES_10 + ST_TYPES_11:
            raise ValueError('invalid value for unauthorized_status field')

        super(ServerConfig, self).__init__(options)

    @staticmethod
    def _get_env_config(env=os.environ):
        result = _infinite_dict()
        for key, value in env.items():
            if not key.startswith(ENV_VAR_PREFIX):
                continue
            key = key[len(ENV_VAR_PREFIX):].lstrip('_').lower()
            value = yaml.safe_load(value)

            container = result
            parts = key.split('__')
            for part in parts[:-1]:
                container = container[part]
            container[parts[-1]] = value

        return dict(result)

    @classmethod
    def _load_configs(cls, *configs):
        result = dict()
        for config in configs:
            # read content from path-like object
            if not isinstance(config, dict):
                with open(config) as stream:
                    config = yaml.safe_load(stream=stream)
            result.update(config)
        return result
