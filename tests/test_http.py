
import pytest
import tempfile

from libtaxii import messages_10 as tm10
from libtaxii import messages_11 as tm11
from libtaxii.constants import ST_SUCCESS, ST_NOT_FOUND, ST_FAILURE

from taxii_server.middleware import create_app
from taxii_server.utils import configure_logging

from taxii_server.taxii.http import *

INBOX = dict(
    type = 'inbox',
    description = 'inboxA description',
    destination_collection_required = True,
    address = '/relative/path',
    accept_all_content = True,
    protocol_bindings = ['urn:taxii.mitre.org:protocol:http:1.0', 'urn:taxii.mitre.org:protocol:https:1.0']
)

DISCOVERY = dict(
    type = 'discovery',
    description = 'discoveryA description',
    address = '/relative/discovery',
    advertised_services = ['inboxA', 'discoveryA'],
    protocol_bindings = ['urn:taxii.mitre.org:protocol:http:1.0']
)


SERVICES = {
    'inboxA' : INBOX,
    'discoveryA' : DISCOVERY
}
INSTANCES_CONFIGURED = sum(len(s['protocol_bindings']) for s in SERVICES.values())
MESSAGE_ID = '123'

configure_logging('debug')

@pytest.fixture(scope="module")
def client():
    tempdir = tempfile.mkdtemp()

    server_config = dict(
        db_connection = 'sqlite:///%s/server.db' % tempdir,
        create_tables = True
    )

    app = create_app(server_properties=server_config, services_properties=SERVICES)
    app.config['TESTING'] = True

    return app.test_client()


def prepare_headers(version, https=False):
    headers = dict()
    if version == 10:
        if https:
            headers.update(TAXII_10_HTTPS_Headers)
        else:
            headers.update(TAXII_10_HTTP_Headers)
    elif version == 11:
        if https:
            headers.update(TAXII_11_HTTPS_Headers)
        else:
            headers.update(TAXII_11_HTTP_Headers)
    else:
        raise ValueError('Unknown TAXII message version: %s' % version)

    headers[HTTP_ACCEPT] = HTTP_CONTENT_XML

    return headers


def includes(superset, subset):
    return all(item in superset.items() for item in subset.items())


def is_headers_valid(headers, version, https):
    if version == 10:
        if https:
            return includes(headers, TAXII_10_HTTPS_Headers)
        else:
            return includes(headers, TAXII_10_HTTP_Headers)
    elif version == 11:
        if https:
            return includes(headers, TAXII_11_HTTPS_Headers)
        else:
            return includes(headers, TAXII_11_HTTP_Headers)
    else:
        raise ValueError('Unknown TAXII message version: %s' % version)


def as_tm(version):
    if version == 10:
        return tm10
    elif version == 11:
        return tm11
    else:
        raise ValueError('Unknown TAXII message version: %s' % version)

def test_root_get(client):
    assert client.get('/').status_code == 404


def test_get_not_allowed(client):
    response = client.get(INBOX['address'])
    assert response.status_code == 405


def test_not_accepted_without_headers(client):
    response = client.post(INBOX['address'])
    assert response.status_code == 406


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_status_message_response(client, version, https):

    base_url = '%s://localhost' % ('https' if https else 'http')

    response = client.post(
        INBOX['address'],
        data = 'invalid-body',
        headers = prepare_headers(version, https),
        base_url = base_url
    )

    assert response.status_code == 200
    assert is_headers_valid(response.headers, version, https)

    message = as_tm(version).get_message_from_xml(response.data)

    assert message.status_type == ST_BAD_MESSAGE


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_successful_response(client, version, https):

    request = as_tm(version).DiscoveryRequest(message_id=MESSAGE_ID)
    base_url = '%s://localhost' % ('https' if https else 'http')

    response = client.post(
        DISCOVERY['address'],
        data = request.to_xml(),
        headers = prepare_headers(version=version, https=https),
        base_url = base_url
    )

    assert response.status_code == 200
    assert is_headers_valid(response.headers, version=version, https=https)

    message = as_tm(version).get_message_from_xml(response.data)

    assert isinstance(message, as_tm(version).DiscoveryResponse)
    assert len(message.service_instances) == INSTANCES_CONFIGURED



@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_post_parse_verification(client, version, https):

    headers = prepare_headers(version, https)
    headers[HTTP_X_TAXII_SERVICES] = 'invalid-services-spec'

    request = as_tm(version).DiscoveryRequest(message_id=MESSAGE_ID)
    base_url = '%s://localhost' % ('https' if https else 'http')

    response = client.post(
        DISCOVERY['address'],
        data = request.to_xml(),
        headers = headers,
        base_url = base_url
    )

    assert response.status_code == 200
    assert is_headers_valid(response.headers, version=version, https=https)

    message = as_tm(version).get_message_from_xml(response.data)

    assert message.status_type == ST_FAILURE
    assert message.in_response_to == MESSAGE_ID




