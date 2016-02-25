import pytest

from opentaxii.server import TAXIIServer

from conftest import get_config_for_tests

INBOX = dict(
    id = 'inbox-A',
    type = 'inbox',
    description = 'inboxA description',
    destination_collection_required = 'yes',
    address = '/relative/path',
    accept_all_content = 'yes',
    protocol_bindings = ['urn:taxii.mitre.org:protocol:http:1.0', 'urn:taxii.mitre.org:protocol:https:1.0'],
)

DISCOVERY = dict(
    id = 'discovery-A',
    type = 'discovery',
    description = 'discoveryA description',
    address = '/relative/discovery',
    advertised_services = ['inboxA', 'discoveryA'],
    protocol_bindings = ['urn:taxii.mitre.org:protocol:http:1.0']
)

DISCOVERY_EXTERNAL = dict(
    id = 'discovery-C',
    type = 'discovery',
    description = 'discoveryB description',
    address = 'http://example.com/a/b/c',
    protocol_bindings = ['urn:taxii.mitre.org:protocol:http:1.0']
)

INTERNAL_SERVICES = [INBOX, DISCOVERY]
SERVICES = INTERNAL_SERVICES + [DISCOVERY_EXTERNAL]

DOMAIN = 'example.com'

@pytest.fixture(scope='module')
def server():
    config = get_config_for_tests(DOMAIN)
    server = TAXIIServer(config)

    server.persistence.create_services_from_object(SERVICES)

    return server


def test_services_configured(server):
    assert len(server.get_services()) == len(SERVICES)

    with_paths = filter(lambda x: x.path, server.get_services())

    assert len(with_paths) == len(INTERNAL_SERVICES)
    assert all(map(lambda x: x.address.startswith(DOMAIN), with_paths))

