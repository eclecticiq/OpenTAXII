import json

import pytest

from opentaxii.middleware import create_app
from opentaxii.server import TAXIIServer
from opentaxii.utils import get_config_for_tests


HEALTH_PATH = '/management/health'


@pytest.fixture()
def client():
    config = get_config_for_tests('some.com')

    server = TAXIIServer(config)

    app = create_app(server)
    app.config['TESTING'] = True

    return app.test_client()


@pytest.mark.parametrize("https", [True, False])
def test_get_health(client, https):
    base_url = '%s://localhost' % ('https' if https else 'http')

    # Invalid credentials
    response = client.get(
        HEALTH_PATH,

        base_url=base_url
    )
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data.get('alive') == True
