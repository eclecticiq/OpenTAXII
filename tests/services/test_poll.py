import pytest
import tempfile

from datetime import datetime

from libtaxii import messages_10 as tm10
from libtaxii import messages_11 as tm11
from libtaxii import constants

from taxii_server.server import TAXIIServer
from taxii_server.options import ServerConfig
from taxii_server.taxii import exceptions

from taxii_server.data.sql import SQLDB
from taxii_server.data import DataManager
from taxii_server.taxii import entities

from utils import get_service, prepare_headers, as_tm, persist_content
from fixtures import *


@pytest.fixture
def manager():
    db_connection = 'sqlite://' # in-memory DB

    config = ServerConfig(services_properties=SERVICES)
    manager = DataManager(config=config, api=SQLDB(db_connection, create_tables=True))
    return manager


@pytest.fixture()
def server(manager):

    server = TAXIIServer(DOMAIN, data_manager=manager)

    services = ['poll-A', 'collection-management-A']

    for coll in COLLECTIONS_B:
        coll = manager.save_collection(coll)
        manager.assign_collection(coll.id, services_ids=services)

    return server


def prepare_request(collection_name, version, only_count=False, bindings=[]):

    if version == 11:
        content_bindings = map(tm11.ContentBinding, bindings)
        return tm11.PollRequest(
            message_id = MESSAGE_ID,
            collection_name = collection_name,
            poll_parameters = tm11.PollParameters(
                response_type = constants.RT_FULL if not only_count else constants.RT_COUNT_ONLY,
                content_bindings = content_bindings,
            )
        )
    elif version == 10:
        content_bindings = bindings
        return tm10.PollRequest(
            message_id = MESSAGE_ID,
            feed_name = collection_name,
            content_bindings = content_bindings
        )


def prepare_fulfilment_request(collection_name, result_id, part_number):

    return tm11.PollFulfillmentRequest(
        message_id = MESSAGE_ID,
        collection_name = collection_name,
        result_id = result_id,
        result_part_number = part_number
    )



@pytest.mark.parametrize(("https", "version"), [
    (True, 11),
    (False, 11),
    pytest.mark.xfail((True, 10), raises=exceptions.StatusMessageException),
    pytest.mark.xfail((False, 10), raises=exceptions.StatusMessageException)
])
def test_poll_empty_response(server, version, https):

    service = get_service(server, 'poll-A')

    headers = prepare_headers(version, https)
    request = prepare_request(collection_name=COLLECTION_OPEN, version=version)

    response = service.process(headers, request)

    assert isinstance(response, as_tm(version).PollResponse)

    assert response.record_count.record_count == 0
    assert not response.record_count.partial_count


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_poll_get_content(server, version, manager, https):

    service = get_service(server, 'poll-A')
    original = persist_content(manager, COLLECTION_ONLY_STIX, service.id)

    # wrong collection
    headers = prepare_headers(version, https)
    request = prepare_request(collection_name=COLLECTION_STIX_AND_CUSTOM,
            version=version)

    response = service.process(headers, request)

    assert isinstance(response, as_tm(version).PollResponse)
    assert len(response.content_blocks) == 0

    # right collection
    headers = prepare_headers(version, https)
    request = prepare_request(collection_name=COLLECTION_ONLY_STIX,
            version=version)

    response = service.process(headers, request)

    assert isinstance(response, as_tm(version).PollResponse)
    assert len(response.content_blocks) == 1

    block = response.content_blocks[0]

    assert original.content == block.content
    assert original.timestamp_label == block.timestamp_label


@pytest.mark.parametrize("https", [True, False])
def test_poll_get_content_count(server, manager, https):

    version = 11

    service = get_service(server, 'poll-A')

    blocks_amount = 10

    for i in range(blocks_amount):
        persist_content(manager, COLLECTION_OPEN, service.id)

    headers = prepare_headers(version, https)

    # count-only request
    request = prepare_request(collection_name=COLLECTION_OPEN, only_count=True, version=version)

    response = service.process(headers, request)

    assert isinstance(response, tm11.PollResponse)

    assert response.record_count.record_count == blocks_amount
    assert response.record_count.partial_count is False
    assert len(response.content_blocks) == 0



@pytest.mark.parametrize("https", [True, False])
def test_poll_max_count_max_size(server, manager, https):

    version = 11

    service = get_service(server, 'poll-A')

    blocks_amount = 30

    for i in range(blocks_amount):
        persist_content(manager, COLLECTION_OPEN, service.id)

    headers = prepare_headers(version, https)

    # count-only request
    request = prepare_request(collection_name=COLLECTION_OPEN, only_count=True, version=version)
    response = service.process(headers, request)

    assert isinstance(response, tm11.PollResponse)

    assert response.record_count.record_count == POLL_MAX_COUNT
    assert len(response.content_blocks) == 0


    # content request
    request = prepare_request(collection_name=COLLECTION_OPEN, version=version)
    response = service.process(headers, request)

    assert isinstance(response, tm11.PollResponse)

    assert response.record_count.record_count == POLL_MAX_COUNT
    assert response.record_count.partial_count is True
    assert len(response.content_blocks) == POLL_RESULT_SIZE

    assert response.more is True
    assert response.result_id is not None


@pytest.mark.parametrize("https", [True, False])
def test_poll_fulfilment_request(server, manager, https):

    version = 11

    service = get_service(server, 'poll-A')

    blocks_amount = 30

    for i in range(blocks_amount):
        persist_content(manager, COLLECTION_OPEN, service.id)

    headers = prepare_headers(version, https)

    # first content request
    request = prepare_request(collection_name=COLLECTION_OPEN, version=version)
    response = service.process(headers, request)

    assert isinstance(response, tm11.PollResponse)

    assert response.record_count.record_count == POLL_MAX_COUNT
    assert response.record_count.partial_count is True
    assert len(response.content_blocks) == POLL_RESULT_SIZE

    assert response.more is True
    assert response.result_id is not None

    # poll fullfilment request
    result_id = response.result_id
    part_number = 2
    request = prepare_fulfilment_request(COLLECTION_OPEN, result_id, part_number)
    response = service.process(headers, request)

    assert isinstance(response, tm11.PollResponse)

    assert response.record_count.record_count == POLL_MAX_COUNT
    assert response.record_count.partial_count is True
    assert len(response.content_blocks) == (blocks_amount - POLL_RESULT_SIZE)

    assert response.more is False
    assert response.result_id == result_id


    # poll fullfilment request over the top
    result_id = response.result_id
    part_number = 3
    request = prepare_fulfilment_request(COLLECTION_OPEN, result_id, part_number)
    response = service.process(headers, request)

    assert isinstance(response, tm11.PollResponse)

    assert response.record_count.record_count == POLL_MAX_COUNT
    assert response.record_count.partial_count is True
    assert len(response.content_blocks) == 0

    assert response.more is False
    assert response.result_id == result_id

