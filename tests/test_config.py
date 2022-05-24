import os
import tempfile

import pytest
from opentaxii.config import ServerConfig

BACKWARDS_COMPAT_CONFIG = """
---
dummy: some
persistence_api:
  class: some.test.PersistenceClass
  parameters:
    a: 1
    b: 2
auth_api:
  class: other.test.AuthClass
  parameters:
    c: 3
"""
COMBINED_CONFIG = """
---
dummy: some
auth_api:
  class: other.test.AuthClass
  parameters:
    c: 3
taxii1:
  persistence_api:
    class: some.test.PersistenceClass
    parameters:
      a: 1
      b: 2
taxii2:
  persistence_api:
    class: some.test.Taxii2PersistenceClass
    parameters:
      a: 1
      b: 2
  max_content_length: 1024
  public_discovery: true
"""
TAXII2_CONFIG = """
---
dummy: some
persistence_api:
  class: some.test.PersistenceClass
auth_api:
  class: other.test.AuthClass
  parameters:
    c: 3
taxii1:
taxii2:
  persistence_api:
    class: some.test.Taxii2PersistenceClass
    parameters:
      a: 1
      b: 2
  max_content_length: 1024
  public_discovery: true
"""
DEFAULT_BASE_VALUES = {
    "domain": "localhost:9000",
    "support_basic_auth": True,
    "return_server_error_details": False,
    "logging": {"opentaxii": "info", "root": "info"},
    "auth_api": {
        "class": "other.test.AuthClass",
        "parameters": {
            "c": 3,
            "create_tables": True,
            "db_connection": "sqlite:////tmp/auth.db",
            "secret": "SECRET-STRING-NEEDS-TO-BE-CHANGED",
            "token_ttl_secs": 3600,
        },
    },
}
DEFAULT_TAXII1_VALUES = {
    "save_raw_inbox_messages": True,
    "xml_parser_supports_huge_tree": True,
    "unauthorized_status": "UNAUTHORIZED",
    "hooks": None,
    "count_blocks_in_poll_responses": False,
}
TAXII1_VALUES = {
    "persistence_api": {
        "class": "some.test.PersistenceClass",
        "parameters": {
            "a": 1,
            "b": 2,
            "create_tables": True,
            "db_connection": "sqlite:////tmp/data.db",
        },
    },
}
TAXII2_VALUES = {
    "persistence_api": {
        "class": "some.test.Taxii2PersistenceClass",
        "parameters": {
            "a": 1,
            "b": 2,
        },
    },
    "max_content_length": 1024,
    "public_discovery": True,
}
EXPECTED_VALUES = {
    BACKWARDS_COMPAT_CONFIG: {
        **DEFAULT_BASE_VALUES,
        "taxii1": {
            **DEFAULT_TAXII1_VALUES,
            **TAXII1_VALUES,
        },
        "taxii2": None,
    },
    COMBINED_CONFIG: {
        **DEFAULT_BASE_VALUES,
        "taxii1": {
            **DEFAULT_TAXII1_VALUES,
            **TAXII1_VALUES,
        },
        "taxii2": {
            **TAXII2_VALUES,
        },
    },
    TAXII2_CONFIG: {
        **DEFAULT_BASE_VALUES,
        "taxii1": None,
        "taxii2": {
            **TAXII2_VALUES,
        },
    },
}
DEPRECATION_WARNING = {
    BACKWARDS_COMPAT_CONFIG: True,
    COMBINED_CONFIG: False,
    TAXII2_CONFIG: False,
}
TAXII2_ONLY_WARNING = {
    BACKWARDS_COMPAT_CONFIG: False,
    COMBINED_CONFIG: False,
    TAXII2_CONFIG: True,
}


@pytest.fixture(
    scope="module",
    params=[BACKWARDS_COMPAT_CONFIG, COMBINED_CONFIG, TAXII2_CONFIG],
    ids=["BACKWARDS_COMPAT_CONFIG", "COMBINED_CONFIG", "TAXII2_CONFIG"],
)
def config_file_name_expected_value(request):
    config = request.param
    f = tempfile.NamedTemporaryFile(delete=False)
    f.write(config.encode("utf-8"))
    f.close()
    yield f.name, EXPECTED_VALUES[config], DEPRECATION_WARNING[
        config
    ], TAXII2_ONLY_WARNING[config]
    os.unlink(f.name)


def test_custom_config_file(config_file_name_expected_value):
    (
        config_file_name,
        expected_value,
        deprecation_warning,
        taxii2_only_warning,
    ) = config_file_name_expected_value
    warning_classes = (UserWarning,)
    if deprecation_warning or taxii2_only_warning:
        warning_classes += (DeprecationWarning,)
    expected_warnings = {"Ignoring invalid configuration item 'dummy'."}
    if deprecation_warning:
        expected_warnings |= {
            f"Setting taxii1 attributes at top level is deprecated. Please nest '{key}' inside 'taxii1'."
            for key in ["persistence_api"]
        }
    if taxii2_only_warning:
        expected_warnings |= {
            f"Running in taxii2-only mode. Dropping deprecated top level taxii1 attribute '{key}'."
            for key in ["persistence_api"]
        }
    with pytest.warns(warning_classes) as warnings:
        config = ServerConfig(extra_configs=[config_file_name])
    assert dict(config) == expected_value
    assert set(str(warning.message) for warning in warnings) == expected_warnings


BACKWARDS_COMPAT_ENVVARS = {
    "input": {
        "OPENTAXII_DOMAIN": "hostname:1337",
        "OPENTAXII__SUPPORT_BASIC_AUTH": "yes",
        "OPENTAXII__PERSISTENCE_API__CLASS": "something.Else",
        "OPENTAXII__PERSISTENCE_API__OTHER": "1",
    },
    "expected": {
        "domain": "hostname:1337",
        "support_basic_auth": True,
        "taxii1": {"persistence_api": {"class": "something.Else", "other": 1}},
    },
}
COMBINED_ENVVARS = {
    "input": {
        "OPENTAXII__TAXII1__PERSISTENCE_API__CLASS": "something.Else",
        "OPENTAXII__TAXII1__PERSISTENCE_API__OTHER": "1",
        "OPENTAXII__TAXII2__PERSISTENCE_API__CLASS": "something.Else2",
        "OPENTAXII__TAXII2__PERSISTENCE_API__OTHER": "2",
        "OPENTAXII__TAXII2__MAX_CONTENT_LENGTH": "1024",
    },
    "expected": {
        "taxii1": {"persistence_api": {"class": "something.Else", "other": 1}},
        "taxii2": {
            "persistence_api": {"class": "something.Else2", "other": 2},
            "max_content_length": 1024,
        },
    },
}
TAXII2_ENVVARS = {
    "input": {
        "OPENTAXII__TAXII2__PERSISTENCE_API__CLASS": "something.Else2",
        "OPENTAXII__TAXII2__PERSISTENCE_API__OTHER": "2",
        "OPENTAXII__TAXII2__MAX_CONTENT_LENGTH": "1024",
    },
    "expected": {
        "taxii2": {
            "persistence_api": {"class": "something.Else2", "other": 2},
            "max_content_length": 1024,
        },
    },
}


@pytest.fixture(
    scope="module",
    params=[BACKWARDS_COMPAT_ENVVARS, COMBINED_ENVVARS, TAXII2_ENVVARS],
    ids=["BACKWARDS_COMPAT_ENVVARS", "COMBINED_ENVVARS", "TAXII2_ENVVARS"],
)
def envvars_expected_value(request):
    yield request.param["input"], request.param["expected"]


def test_env_vars_config(envvars_expected_value):
    envvars, expected_value = envvars_expected_value
    assert (
        ServerConfig._clean_options(ServerConfig._get_env_config(env=envvars))
        == expected_value
    )
