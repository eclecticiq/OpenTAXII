import pytest

from opentaxii.taxii.converters import dict_to_service_entity

from fixtures import DOMAIN

INBOX = dict(
    id='inbox-A',
    type='inbox',
    description='inboxA description',
    destination_collection_required='yes',
    address='/relative/path',
    accept_all_content='yes',
    protocol_bindings=[
        'urn:taxii.mitre.org:protocol:http:1.0',
        'urn:taxii.mitre.org:protocol:https:1.0'],
)

DISCOVERY = dict(
    id='discovery-A',
    type='discovery',
    description='discoveryA description',
    address='/relative/discovery',
    advertised_services=['inboxA', 'discoveryA'],
    protocol_bindings=['urn:taxii.mitre.org:protocol:http:1.0']
)

DISCOVERY_EXTERNAL = dict(
    id='discovery-C',
    type='discovery',
    description='discoveryB description',
    address='http://example.com/a/b/c',
    protocol_bindings=['urn:taxii.mitre.org:protocol:http:1.0']
)

INTERNAL_SERVICES = [INBOX, DISCOVERY]
SERVICES = INTERNAL_SERVICES + [DISCOVERY_EXTERNAL]


@pytest.fixture(autouse=True)
def local_services(server):
    for service in SERVICES:
        server.persistence.update_service(dict_to_service_entity(service))


def test_services_configured(server):
    assert len(server.get_services()) == len(SERVICES)

    with_paths = [
        s for s in server.get_services()
        if s.path]

    assert len(with_paths) == len(INTERNAL_SERVICES)
    assert all([
        p.address.startswith(DOMAIN) for p in with_paths])
