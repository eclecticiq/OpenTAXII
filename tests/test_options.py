import pytest

from opentaxii.taxii.http import HTTP_X_TAXII_CONTENT_TYPES

DISCOVERY = dict(
    id='discovery-A',
    type='discovery',
    description='discoveryA description',
    address='/path/discovery',
    advertised_services=[],
    protocol_bindings=['urn:taxii.mitre.org:protocol:http:1.0'],
    authentication_required=False,
)

SERVICES = [DISCOVERY]


@pytest.fixture(autouse=True)
def prepare_server(server):
    server.persistence.create_services_from_object(SERVICES)


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_options_request(server, client, version, https):

    base_url = '%s://localhost' % ('https' if https else 'http')

    response = client.options(
        DISCOVERY['address'],
        base_url=base_url
    )

    assert response.status_code == 200
    assert HTTP_X_TAXII_CONTENT_TYPES in response.headers

    value = response.headers[HTTP_X_TAXII_CONTENT_TYPES]

    versions = value.split(',')

    service = server.get_service(DISCOVERY['id'])
    service_bindings = service.supported_message_bindings

    assert len(versions) == len(service_bindings)
