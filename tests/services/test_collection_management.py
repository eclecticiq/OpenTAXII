import pytest

from opentaxii.taxii import entities

from utils import prepare_headers, as_tm, persist_content
from fixtures import (
    SERVICES, COLLECTIONS_B, MESSAGE_ID, COLLECTION_OPEN, COLLECTION_ONLY_STIX,
    COLLECTION_STIX_AND_CUSTOM, COLLECTION_DISABLED)

ASSIGNED_SERVICES = ['collection-management-A', 'inbox-A', 'inbox-B', 'poll-A']

ASSIGNED_INBOX_INSTANCES = sum(
    len(s['protocol_bindings'])
    for s in SERVICES
    if s['id'] in ASSIGNED_SERVICES and s['id'].startswith('inbox'))

ASSIGNED_SUBSCTRIPTION_INSTANCES = sum(
    len(s['protocol_bindings'])
    for s in SERVICES
    if s['id'] in ASSIGNED_SERVICES and s['id'].startswith('collection-'))


@pytest.fixture(autouse=True)
def prepare_server(server, services):
    for coll in COLLECTIONS_B:
        coll = server.persistence.create_collection(coll)
        server.persistence.set_collection_services(
            coll.id, service_ids=ASSIGNED_SERVICES)


def prepare_request(version):
    module = as_tm(version)
    if version == 11:
        return module.CollectionInformationRequest(message_id=MESSAGE_ID)
    else:
        return module.FeedInformationRequest(message_id=MESSAGE_ID)


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_collections(server, version, https):

    service = server.get_service('collection-management-A')

    headers = prepare_headers(version, https)
    request = prepare_request(version)
    response = service.process(headers, request)

    names = [c.name for c in COLLECTIONS_B]

    if version == 11:
        assert isinstance(
            response, as_tm(version).CollectionInformationResponse)
        assert len(response.collection_informations) == len(COLLECTIONS_B)

        for c in response.collection_informations:
            assert c.collection_name in names

    else:
        assert isinstance(response, as_tm(version).FeedInformationResponse)
        assert len(response.feed_informations) == len(COLLECTIONS_B)

        for c in response.feed_informations:
            assert c.feed_name in names


@pytest.mark.parametrize("https", [True, False])
def test_collections_inboxes(server, https):

    version = 11
    service = server.get_service('collection-management-A')

    headers = prepare_headers(version, https)
    request = prepare_request(version)
    response = service.process(headers, request)

    for coll in response.collection_informations:
        inboxes = coll.receiving_inbox_services

        assert len(inboxes) == ASSIGNED_INBOX_INSTANCES


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_collections_subscribe_instances(server, version, https):

    service = server.get_service('collection-management-A')

    headers = prepare_headers(version, https)
    request = prepare_request(version)
    response = service.process(headers, request)

    if version == 11:
        collections = response.collection_informations
    else:
        collections = response.feed_informations

    for c in collections:
        assert len(c.subscription_methods) == ASSIGNED_SUBSCTRIPTION_INSTANCES


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_collection_supported_content(server, version, https):

    service = server.get_service('collection-management-A')

    headers = prepare_headers(version, https)
    request = prepare_request(version)
    response = service.process(headers, request)

    if version == 11:

        def get_coll(name):
            return next(
                c for c in response.collection_informations
                if c.collection_name == name)

        assert (
            get_coll(COLLECTION_OPEN).collection_type ==
            entities.CollectionEntity.TYPE_SET)

    else:
        def get_coll(name):
            return next(
                c for c in response.feed_informations
                if c.feed_name == name)

    assert len(get_coll(COLLECTION_OPEN).supported_contents) == 0

    assert len(get_coll(COLLECTION_ONLY_STIX).supported_contents) == 1
    assert len(get_coll(COLLECTION_STIX_AND_CUSTOM).supported_contents) == 2

    assert not get_coll(COLLECTION_DISABLED).available


@pytest.mark.parametrize("https", [True, False])
def test_collections_volume(server, https):

    version = 11

    service = server.get_service('collection-management-A')

    headers = prepare_headers(version, https)
    request = prepare_request(version)

    # querying empty collection
    response = service.process(headers, request)

    collection = next(
        c for c in response.collection_informations
        if c.collection_name == COLLECTION_OPEN)

    assert collection.collection_volume == 0

    blocks_amount = 10

    for i in range(blocks_amount):
        persist_content(server.persistence, COLLECTION_OPEN, service.id)

    # querying filled collection
    response = service.process(headers, request)

    collection = next(
        c for c in response.collection_informations
        if c.collection_name == COLLECTION_OPEN)

    assert collection.collection_volume == blocks_amount


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_collections_defined_supported_content(server, version, https):

    service = server.get_service('collection-management-A')

    headers = prepare_headers(version, https)
    request = prepare_request(version)
    response = service.process(headers, request)

    if version == 10:
        coll = response.feed_informations[0]
    else:
        coll = response.collection_informations[0]

    # 1 poll service with 2 defined protocol bindings
    assert len(coll.polling_service_instances) == 2
