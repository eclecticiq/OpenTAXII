import pytest

from libtaxii import messages_10 as tm10
from libtaxii import messages_11 as tm11
from libtaxii.constants import (
    RT_COUNT_ONLY, RT_FULL, CB_STIX_XML_111, ACT_SUBSCRIBE)

from opentaxii.taxii import exceptions

from utils import (
    prepare_headers, as_tm, persist_content, prepare_subscription_request)

from fixtures import (
    COLLECTIONS_B, MESSAGE_ID, COLLECTION_OPEN,
    COLLECTION_DISABLED, COLLECTION_ONLY_STIX,
    COLLECTION_STIX_AND_CUSTOM, CUSTOM_CONTENT_BINDING,
    POLL_MAX_COUNT, POLL_RESULT_SIZE)


@pytest.fixture(autouse=True)
def prepare_server(server, services):
    services = ['poll-A', 'collection-management-A']
    for coll in COLLECTIONS_B:
        coll = server.persistence.create_collection(coll)
        server.persistence.set_collection_services(
            coll.id, service_ids=services)
    return server


def prepare_request(collection_name, version, count_only=False,
                    bindings=[], subscription_id=None):

    if version == 11:
        content_bindings = [tm11.ContentBinding(b) for b in bindings]
        if subscription_id:
            poll_parameters = None
        else:
            poll_parameters = tm11.PollParameters(
                response_type=(
                    RT_FULL if not count_only else RT_COUNT_ONLY),
                content_bindings=content_bindings)
        return tm11.PollRequest(
            message_id=MESSAGE_ID,
            collection_name=collection_name,
            subscription_id=subscription_id,
            poll_parameters=poll_parameters
        )
    elif version == 10:
        content_bindings = bindings
        return tm10.PollRequest(
            message_id=MESSAGE_ID,
            feed_name=collection_name,
            content_bindings=content_bindings,
            subscription_id=subscription_id
        )


def prepare_fulfilment_request(collection_name, result_id, part_number):
    return tm11.PollFulfillmentRequest(
        message_id=MESSAGE_ID,
        collection_name=collection_name,
        result_id=result_id,
        result_part_number=part_number
    )


@pytest.mark.parametrize(("https", "version", "count_blocks"), [
    (True, 11, True), (False, 11, False),
    (True, 10, False), (False, 10, False),
])
def test_poll_empty_response(server, version, https, count_blocks):

    server.config['count_blocks_in_poll_responses'] = count_blocks

    service = server.get_service('poll-A')

    headers = prepare_headers(version, https)
    request = prepare_request(
        collection_name=COLLECTION_OPEN, version=version)

    if version == 11:
        response = service.process(headers, request)

        assert isinstance(response, as_tm(version).PollResponse)

        if count_blocks:
            assert response.record_count.record_count == 0
            assert not response.record_count.partial_count
        else:
            assert response.record_count is None

    else:
        # COLLECTION_OPEN type (SET) is not supported in TAXII 1.0
        with pytest.raises(exceptions.StatusMessageException):
            response = service.process(headers, request)

    server.config['count_blocks_in_poll_responses'] = True


@pytest.mark.parametrize(
    ("https", "version"),
    [(True, 11), (False, 11), (True, 10), (False, 10)])
def test_poll_collection_not_available(server, version, https):

    service = server.get_service('poll-A')

    headers = prepare_headers(version, https)
    request = prepare_request(
        collection_name=COLLECTION_DISABLED, version=version)

    with pytest.raises(exceptions.StatusMessageException):
        service.process(headers, request)


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_poll_get_content(server, version, https):

    service = server.get_service('poll-A')
    original = persist_content(
        server.persistence, COLLECTION_ONLY_STIX,
        service.id, binding=CB_STIX_XML_111)

    # wrong collection
    headers = prepare_headers(version, https)
    request = prepare_request(
        collection_name=COLLECTION_STIX_AND_CUSTOM,
        version=version)

    response = service.process(headers, request)

    assert isinstance(response, as_tm(version).PollResponse)
    assert len(response.content_blocks) == 0

    # right collection
    headers = prepare_headers(version, https)
    request = prepare_request(
        collection_name=COLLECTION_ONLY_STIX,
        version=version)

    response = service.process(headers, request)

    assert isinstance(response, as_tm(version).PollResponse)
    assert len(response.content_blocks) == 1

    block = response.content_blocks[0]

    assert original.content == block.content.encode('utf-8')
    assert original.timestamp_label == block.timestamp_label

    # right collection and request with wrong content_type
    headers = prepare_headers(version, https)
    request = prepare_request(
        collection_name=COLLECTION_ONLY_STIX,
        version=version, bindings=[CUSTOM_CONTENT_BINDING])

    with pytest.raises(exceptions.StatusMessageException):
        service.process(headers, request)


@pytest.mark.parametrize(
    ("https", "count_blocks"),
    [(True, True), (False, True), (True, False), (False, False)])
def test_poll_get_content_count(server, https, count_blocks):
    version = 11
    server.config['count_blocks_in_poll_responses'] = count_blocks
    service = server.get_service('poll-A')

    blocks_amount = 10

    for i in range(blocks_amount):
        persist_content(server.persistence, COLLECTION_OPEN, service.id)

    headers = prepare_headers(version, https)

    # count-only request
    request = prepare_request(
        collection_name=COLLECTION_OPEN, count_only=True, version=version)
    response = service.process(headers, request)

    assert isinstance(response, tm11.PollResponse)

    if count_blocks:
        assert response.record_count.record_count == blocks_amount
        assert not response.record_count.partial_count
        assert len(response.content_blocks) == 0
    else:
        assert response.record_count is None
    server.config['count_blocks_in_poll_responses'] = True


@pytest.mark.parametrize(
    ("https", "count_blocks"),
    [(True, True), (False, True), (True, False), (False, False)])
def test_poll_max_count_max_size(server, https, count_blocks):

    version = 11
    server.config['count_blocks_in_poll_responses'] = count_blocks

    service = server.get_service('poll-A')

    blocks_amount = 30

    for i in range(blocks_amount):
        persist_content(server.persistence, COLLECTION_OPEN, service.id)

    headers = prepare_headers(version, https)

    # count-only request
    request = prepare_request(collection_name=COLLECTION_OPEN,
                              count_only=True, version=version)
    response = service.process(headers, request)

    assert isinstance(response, tm11.PollResponse)

    if count_blocks:
        assert response.record_count.record_count == POLL_MAX_COUNT
    else:
        assert response.record_count is None
    assert len(response.content_blocks) == 0

    # content request
    request = prepare_request(collection_name=COLLECTION_OPEN, version=version)
    response = service.process(headers, request)
    assert isinstance(response, tm11.PollResponse)

    if count_blocks:
        assert response.record_count.record_count == POLL_MAX_COUNT
        assert response.record_count.partial_count is True
        assert len(response.content_blocks) == POLL_RESULT_SIZE
    else:
        assert response.record_count is None

    assert response.more is True
    assert response.result_id
    server.config['count_blocks_in_poll_responses'] = True


@pytest.mark.parametrize(
    ("https", "count_blocks"),
    [(True, True), (False, True), (True, False), (False, False)])
def test_poll_fulfilment_request(server, https, count_blocks):
    server.config['count_blocks_in_poll_responses'] = count_blocks
    version = 11
    service = server.get_service('poll-A')

    blocks_amount = 30

    for i in range(blocks_amount):
        persist_content(server.persistence, COLLECTION_OPEN, service.id)

    headers = prepare_headers(version, https)

    # first content request
    request = prepare_request(collection_name=COLLECTION_OPEN, version=version)
    response = service.process(headers, request)

    assert isinstance(response, tm11.PollResponse)

    if count_blocks:
        assert response.record_count.record_count == POLL_MAX_COUNT
        assert response.record_count.partial_count is True
        assert len(response.content_blocks) == POLL_RESULT_SIZE
    else:
        assert response.record_count is None

    assert response.more is True
    assert response.result_id

    # poll fullfilment request
    result_id = response.result_id
    part_number = 2
    request = prepare_fulfilment_request(
        COLLECTION_OPEN, result_id, part_number)
    response = service.process(headers, request)

    assert isinstance(response, tm11.PollResponse)

    if count_blocks:
        assert response.record_count.record_count == POLL_MAX_COUNT
        assert response.record_count.partial_count is True
    else:
        assert response.record_count is None

    assert len(response.content_blocks) == (blocks_amount - POLL_RESULT_SIZE)

    assert not response.more
    assert response.result_id == result_id

    # poll fullfilment request over the top
    result_id = response.result_id
    part_number = 3
    request = prepare_fulfilment_request(
        COLLECTION_OPEN, result_id, part_number)
    response = service.process(headers, request)
    assert isinstance(response, tm11.PollResponse)

    if count_blocks:
        assert response.record_count.record_count == POLL_MAX_COUNT
        assert response.record_count.partial_count is True
    else:
        assert response.record_count is None

    assert len(response.content_blocks) == 0

    assert not response.more
    assert response.result_id == result_id
    server.config['count_blocks_in_poll_responses'] = True


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_subscribe_and_poll(server, version, https):

    server.config['count_blocks_in_poll_responses'] = True

    subs_service = server.get_service('collection-management-A')
    poll_service = server.get_service('poll-A')

    collection = COLLECTION_ONLY_STIX

    blocks_amount = 10
    for i in range(blocks_amount):
        persist_content(server.persistence, collection, poll_service.id)

    headers = prepare_headers(version, https)

    params = dict(
        response_type=RT_COUNT_ONLY,
        content_bindings=[CB_STIX_XML_111, CUSTOM_CONTENT_BINDING])

    subs_request = prepare_subscription_request(
        collection=collection,
        action=ACT_SUBSCRIBE,
        version=version,
        params=params)

    subs_response = subs_service.process(headers, subs_request)

    assert len(subs_response.subscription_instances) == 1

    subscription = subs_response.subscription_instances[0]
    assert subscription.subscription_id

    # response type (count_only==False) should be ignored
    # for TAXII 1.1 requests
    poll_request = prepare_request(
        collection_name=collection,
        count_only=False,
        subscription_id=subscription.subscription_id,
        version=version)

    poll_response = poll_service.process(headers, poll_request)

    if version == 11:
        assert poll_response.record_count.record_count == blocks_amount
        assert not poll_response.record_count.partial_count

        assert len(poll_response.content_blocks) == 0
        assert poll_response.subscription_id == subscription.subscription_id
    else:
        assert len(poll_response.content_blocks) == blocks_amount
