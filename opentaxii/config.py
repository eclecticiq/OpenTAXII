import os
import anyconfig
import structlog

log = structlog.get_logger(__name__)

current_dir = os.path.dirname(os.path.realpath(__file__))

CONFIG_ENV_VAR = 'TAXII_SERVER_CONFIG'
DEFAULT_CONFIG = os.path.join(current_dir, 'defaults.yml')


class ServerConfig(dict):

    def __init__(self, default_config_file=DEFAULT_CONFIG, optional_env_var=CONFIG_ENV_VAR):

        config_paths = [default_config_file]

        env_var_path = os.environ.get(optional_env_var)
        if env_var_path:
            config_paths.append(env_var_path)

        options = anyconfig.load(config_paths, forced_type="yaml", ignore_missing=False)

        self.update(options)



