import pytest

from opentaxii.server import TAXIIServer
from opentaxii.config import ServerConfig
from opentaxii.utils import create_manager, create_services_from_config

INBOX = dict(
    type = 'inbox',
    description = 'inboxA description',
    destination_collection_required = 'yes',
    address = '/relative/path',
    accept_all_content = 'yes',
    protocol_bindings = ['urn:taxii.mitre.org:protocol:http:1.0', 'urn:taxii.mitre.org:protocol:https:1.0']
)

DISCOVERY = dict(
    type = 'discovery',
    description = 'discoveryA description',
    address = '/relative/discovery',
    advertised_services = ['inboxA', 'discoveryA'],
    protocol_bindings = ['urn:taxii.mitre.org:protocol:http:1.0']
)

DISCOVERY_EXTERNAL = dict(
    type = 'discovery',
    description = 'discoveryB description',
    address = 'http://example.com/a/b/c',
    protocol_bindings = ['urn:taxii.mitre.org:protocol:http:1.0']
)

INTERNAL_SERVICES = [INBOX, DISCOVERY]

SERVICES = {
    'inboxA' : INBOX,
    'discoveryA' : DISCOVERY,
    'discoveryB' : DISCOVERY_EXTERNAL
}

DOMAIN = 'example.com'

@pytest.fixture(scope='module')
def server():

    config = ServerConfig()
    config.update_persistence_api_config(
        'opentaxii.persistence.sqldb.SQLDatabaseAPI', {
            'db_connection' : 'sqlite://', # in-memory DB
            'create_tables' : True
        }
    )
    config['services'].update(SERVICES)

    manager = create_manager(config)
    create_services_from_config(manager=manager, config=config)

    server = TAXIIServer(DOMAIN, manager=manager)

    return server


def test_services_configured(server):
    assert len(server.services) == len(SERVICES)
    assert len(server.path_to_service) == len(INTERNAL_SERVICES)

    assert server.path_to_service[DISCOVERY['address']].id == 'discoveryA'

    assert all(map(lambda x: x.address.startswith(DOMAIN), server.path_to_service.values()))


