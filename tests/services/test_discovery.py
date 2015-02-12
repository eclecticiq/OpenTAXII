import pytest
import tempfile

from taxii_server.server import TAXIIServer
from taxii_server.options import ServerConfig

from taxii_server.persistence.sql import SQLDB
from taxii_server.persistence import DataStorage

from utils import get_service, prepare_headers, as_tm
from fixtures import *


@pytest.fixture(scope='module')
def server():

    tempdir = tempfile.mkdtemp()
    db_connection = 'sqlite:///%s/server.db' % tempdir
    storage = DataStorage(api=SQLDB(db_connection, create_tables=True))
    
    config = ServerConfig(services_properties=SERVICES)

    server = TAXIIServer(DOMAIN, config.services, storage=storage)

    return server


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_discovery_request(server, version, https):

    request = as_tm(version).DiscoveryRequest(message_id=MESSAGE_ID)
    service = get_service(server, 'discovery-A')

    headers = prepare_headers(version, https)
    response = service.process(headers, request)

    assert len(response.service_instances) == INSTANCES_CONFIGURED
    assert response.in_response_to == MESSAGE_ID

    assert isinstance(response, as_tm(version).DiscoveryResponse)


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_content_bindings_present(server, version, https):

    request = as_tm(version).DiscoveryRequest(message_id=MESSAGE_ID)
    service = get_service(server, 'discovery-A')

    headers = prepare_headers(version, https)
    response = service.process(headers, request)

    assert len(response.service_instances) == INSTANCES_CONFIGURED
    assert response.in_response_to == MESSAGE_ID

    inboxes = filter(lambda s: s.service_type == SVC_INBOX, response.service_instances)

    assert len(inboxes) == 4

    address_a = INBOX_A['address']
    inboxes_a = [i for i in inboxes if i.service_address.endswith(address_a)]
    # inbox_a accepts everything, so inbox_service_accepted_content is empty
    assert all([len(i.inbox_service_accepted_content) == 0 for i in inboxes_a])

    
    address_b = INBOX_B['address']
    inboxes_b = [i for i in inboxes if i.service_address.endswith(address_b)]
    bindings = inboxes_b[0].inbox_service_accepted_content

    if version == 10:
        binding_ids = bindings
    else:
        binding_ids = [b.binding_id for b in bindings]

    assert set(binding_ids) == set(INBOX_B['supported_content'])
    
