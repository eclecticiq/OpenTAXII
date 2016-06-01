import os
import tempfile

import pytest

from opentaxii.config import ServerConfig

CUSTOM_CONFIG = '''
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
'''


@pytest.yield_fixture
def config_file_name(config=CUSTOM_CONFIG):
    f = tempfile.NamedTemporaryFile(delete=False)
    f.write(config.encode('utf-8'))
    f.close()
    yield f.name
    os.unlink(f.name)


def test_custom_config_file(config_file_name):
    config = ServerConfig(extra_configs=[config_file_name])

    assert config['persistence_api']['class'] == 'some.test.PersistenceClass'
    assert set(config['persistence_api']['parameters'].keys()) == {'a', 'b'}

    assert config['auth_api']['class'] == 'other.test.AuthClass'
    assert config['auth_api']['parameters'] == {'c': 3}
