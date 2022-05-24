import os
from collections import defaultdict
from warnings import warn

import yaml
from libtaxii.constants import ST_TYPES_10, ST_TYPES_11

current_dir = os.path.dirname(os.path.realpath(__file__))

ENV_VAR_PREFIX = "OPENTAXII_"
CONFIG_ENV_VAR = "OPENTAXII_CONFIG"
DEFAULT_CONFIG_NAME = "defaults.yml"
DEFAULT_CONFIG = os.path.join(current_dir, DEFAULT_CONFIG_NAME)


def _infinite_dict():
    return defaultdict(_infinite_dict)


def merge(d1, d2):
    for k in d2:
        if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], dict):
            d1[k] = merge(d1[k], d2[k])
        else:
            d1[k] = d2[k]
    return d1


class ServerConfig(dict):
    """Class responsible for loading configuration files.

    This class will load default configuration file (shipped with OpenTAXII)
    and apply user specified configuration file on top of default one.

    Users can specify custom configuration file (YAML formatted) using
    enviromental variable. The variable should contain a full path to
    a custom configuration file.

    :param str optional_env_var: name of the enviromental variable
    :param list extra_configs: list of additional config filenames
    """

    VALID_BASE_OPTIONS = (
        "domain",
        "support_basic_auth",
        "return_server_error_details",
        "logging",
        "auth_api",
        "taxii1",
        "taxii2",
    )
    VALID_TAXII_OPTIONS = ("persistence_api",)
    VALID_TAXII1_OPTIONS = (
        "save_raw_inbox_messages",
        "xml_parser_supports_huge_tree",
        "count_blocks_in_poll_responses",
        "unauthorized_status",
        "hooks",
    )
    VALID_TAXII2_OPTIONS = (
        "contact",
        "description",
        "max_content_length",
        "title",
        "public_discovery",
    )
    ALL_VALID_OPTIONS = VALID_BASE_OPTIONS + VALID_TAXII_OPTIONS + VALID_TAXII1_OPTIONS

    def __init__(self, optional_env_var=CONFIG_ENV_VAR, extra_configs=None):

        # 4. default config
        configs = [DEFAULT_CONFIG]
        # 3. explicit configs
        configs.extend(extra_configs or [])
        # 2. config from OPENTAXII_CONFIG env var path
        env_var_path = os.environ.get(optional_env_var)
        if env_var_path:
            configs.append(env_var_path)
        # 1. config built from env vars
        configs.append(self._get_env_config(optional_env_var=optional_env_var))

        options = self._load_configs(*configs)
        options = self._clean_options(options)
        if (
            options["taxii1"]
            and options["taxii1"]["unauthorized_status"]
            not in ST_TYPES_10 + ST_TYPES_11
        ):
            raise ValueError("invalid value for unauthorized_status field")

        super(ServerConfig, self).__init__(options)

    @staticmethod
    def _get_env_config(env=os.environ, optional_env_var=None):
        result = _infinite_dict()
        for key, value in env.items():
            if not key.startswith(ENV_VAR_PREFIX):
                continue
            if key == optional_env_var:
                continue
            key = key[len(ENV_VAR_PREFIX):].lstrip("_").lower()
            value = yaml.safe_load(value)

            container = result
            parts = key.split("__")
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
            result = merge(result, config)
        return result

    @classmethod
    def _clean_options(cls, options: dict) -> dict:
        # Put taxii and taxii2 keys that are in base level inside taxii1
        # structure for backwards compatibility
        for key in cls.VALID_TAXII1_OPTIONS + cls.VALID_TAXII_OPTIONS:
            if key in options:
                taxii1_dict = options.setdefault("taxii1", {})
                if taxii1_dict is None:
                    # taxii1 explicitly disabled -> taxii2-only mode
                    # drop taxii1 default values
                    warn(
                        f"Running in taxii2-only mode. Dropping deprecated top level taxii1 attribute '{key}'.",
                        DeprecationWarning,
                    )
                    del options[key]
                else:
                    warn(
                        f"Setting taxii1 attributes at top level is deprecated. Please nest '{key}' inside 'taxii1'.",
                        DeprecationWarning,
                    )
                    if key in taxii1_dict and isinstance(taxii1_dict[key], dict):
                        taxii1_dict[key] = merge(taxii1_dict[key], options.pop(key))
                    else:
                        taxii1_dict[key] = options.pop(key)
        # Warn user of invalid keys and remove from dict
        for key in [key for key in options if key not in cls.ALL_VALID_OPTIONS]:
            warn(f"Ignoring invalid configuration item '{key}'.")
            del options[key]
        if "taxii1" in options and options["taxii1"]:
            for key in [
                key
                for key in options["taxii1"]
                if key not in cls.VALID_TAXII_OPTIONS + cls.VALID_TAXII1_OPTIONS
            ]:
                warn(f"Ignoring invalid taxii1 configuration item '{key}'.")
                del options["taxii1"][key]
        if "taxii2" in options and options["taxii2"]:
            for key in [
                key
                for key in options["taxii2"]
                if key not in cls.VALID_TAXII_OPTIONS + cls.VALID_TAXII2_OPTIONS
            ]:
                warn(f"Ignoring invalid taxii2 configuration item '{key}'.")
                del options["taxii2"][key]
        return options
