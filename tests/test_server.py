import concurrent.futures

import pytest
from fixtures import DOMAIN

from opentaxii.persistence import OpenTAXII2PersistenceAPI, Taxii2PersistenceManager
from opentaxii.persistence.sqldb import Taxii2SQLDatabaseAPI
from opentaxii.server import TAXII2Server
from opentaxii.taxii.converters import dict_to_service_entity

INBOX = dict(
    id='inbox-A',
    type='inbox',
    description='inboxA description',
    destination_collection_required='yes',
    address='/relative/path',
    accept_all_content='yes',
    protocol_bindings=[
        'urn:taxii.mitre.org:protocol:http:1.0',
        'urn:taxii.mitre.org:protocol:https:1.0',
    ],
)

DISCOVERY = dict(
    id='discovery-A',
    type='discovery',
    description='discoveryA description',
    address='/relative/discovery',
    advertised_services=['inboxA', 'discoveryA'],
    protocol_bindings=['urn:taxii.mitre.org:protocol:http:1.0'],
)

DISCOVERY_EXTERNAL = dict(
    id='discovery-C',
    type='discovery',
    description='discoveryB description',
    address='http://example.com/a/b/c',
    protocol_bindings=['urn:taxii.mitre.org:protocol:http:1.0'],
)

INTERNAL_SERVICES = [INBOX, DISCOVERY]
SERVICES = INTERNAL_SERVICES + [DISCOVERY_EXTERNAL]


@pytest.fixture()
def local_services(server):
    for service in SERVICES:
        server.servers.taxii1.persistence.update_service(
            dict_to_service_entity(service)
        )


def test_services_configured(server, local_services):
    assert len(server.servers.taxii1.get_services()) == len(SERVICES)

    with_paths = [s for s in server.servers.taxii1.get_services() if s.path]

    assert len(with_paths) == len(INTERNAL_SERVICES)
    assert all([p.address.startswith(DOMAIN) for p in with_paths])


def test_taxii2_configured(server):
    assert server.servers.taxii2 is not None
    assert isinstance(server.servers.taxii2, TAXII2Server)
    assert isinstance(
        server.servers.taxii2.persistence,
        Taxii2PersistenceManager,
    )
    assert isinstance(
        server.servers.taxii2.persistence.api,
        Taxii2SQLDatabaseAPI,
    )
    assert isinstance(
        server.servers.taxii2.persistence.api,
        OpenTAXII2PersistenceAPI,
    )


@pytest.mark.truncate()
def test_multithreaded_access(server, local_services):

    def testfunc():
        server.servers.taxii1.get_services()
        server.servers.taxii1.persistence.api.db.session.commit()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = [executor.submit(testfunc) for _ in range(2)]
        for result in concurrent.futures.as_completed(results):
            assert not result.exception(timeout=5)
