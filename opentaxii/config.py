import os
import anyconfig

current_dir = os.path.dirname(os.path.realpath(__file__))

CONFIG_ENV_VAR = 'OPENTAXII_CONFIG'
DEFAULT_CONFIG_NAME = 'defaults.yml'
DEFAULT_CONFIG = os.path.join(current_dir, DEFAULT_CONFIG_NAME)


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

        config_paths = [DEFAULT_CONFIG]

        if extra_configs:
            config_paths.extend(extra_configs)

        env_var_path = os.environ.get(optional_env_var)
        if env_var_path:
            config_paths.append(env_var_path)

        options = anyconfig.load(
            config_paths, ac_parser='yaml',
            ignore_missing=False, ac_merge=anyconfig.MS_REPLACE)

        self.update(options)
