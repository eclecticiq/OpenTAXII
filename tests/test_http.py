import pytest

from libtaxii.constants import ST_FAILURE, ST_BAD_MESSAGE
from opentaxii.taxii.http import HTTP_X_TAXII_SERVICES
from opentaxii.taxii.converters import dict_to_service_entity

from utils import prepare_headers, is_headers_valid, as_tm

INBOX = dict(
    id='inbox-A',
    type='inbox',
    description='inboxA description',
    destination_collection_required=True,
    address='/relative/path',
    accept_all_content=True,
    protocol_bindings=[
        'urn:taxii.mitre.org:protocol:http:1.0',
        'urn:taxii.mitre.org:protocol:https:1.0']
)

DISCOVERY = dict(
    id='discovery-A',
    type='discovery',
    description='discoveryA description',
    address='/relative/discovery',
    advertised_services=['inbox-A', 'discovery-A', 'discovery-B'],
    protocol_bindings=['urn:taxii.mitre.org:protocol:http:1.0']
)

DISCOVERY_NOT_AVAILABLE = dict(
    id='discovery-B',
    type='discovery',
    description='discoveryA description',
    address='/relative/discovery-b',
    advertised_services=['inbox-A', 'discovery-A'],
    protocol_bindings=['urn:taxii.mitre.org:protocol:http:1.0'],
    available=False
)

SERVICES = [INBOX, DISCOVERY, DISCOVERY_NOT_AVAILABLE]
INSTANCES_CONFIGURED = sum(len(s['protocol_bindings']) for s in SERVICES)
MESSAGE_ID = '123'


@pytest.fixture(autouse=True)
def local_services(server):
    for service in SERVICES:
        server.persistence.update_service(dict_to_service_entity(service))


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
        data='invalid-body',
        headers=prepare_headers(version, https),
        base_url=base_url
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
        data=request.to_xml(),
        headers=prepare_headers(version=version, https=https),
        base_url=base_url
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
        data=request.to_xml(),
        headers=headers,
        base_url=base_url
    )

    assert response.status_code == 200
    assert is_headers_valid(response.headers, version=version, https=https)

    message = as_tm(version).get_message_from_xml(response.data)

    assert message.status_type == ST_FAILURE
    assert message.in_response_to == MESSAGE_ID


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_services_available(client, version, https):

    headers = prepare_headers(version, https)

    request = as_tm(version).DiscoveryRequest(message_id=MESSAGE_ID)
    base_url = '%s://localhost' % ('https' if https else 'http')

    response = client.post(
        DISCOVERY_NOT_AVAILABLE['address'],
        data=request.to_xml(),
        headers=headers,
        base_url=base_url
    )

    assert response.status_code == 200

    message = as_tm(version).get_message_from_xml(response.data)

    assert isinstance(message, as_tm(version).StatusMessage)
    assert message.status_type == ST_FAILURE
