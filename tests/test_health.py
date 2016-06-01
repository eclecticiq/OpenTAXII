import json
import pytest


HEALTH_PATH = '/management/health'


@pytest.mark.parametrize("https", [True, False])
def test_get_health(client, https):
    base_url = '%s://localhost' % ('https' if https else 'http')

    # Invalid credentials
    response = client.get(
        HEALTH_PATH,
        base_url=base_url
    )
    assert response.status_code == 200

    data = json.loads(response.get_data(as_text=True))
    assert data.get('alive')
