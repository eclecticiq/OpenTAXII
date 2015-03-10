import pytest
import tempfile

from opentaxii.server import TAXIIServer
from opentaxii.config import ServerConfig
from opentaxii.taxii import exceptions, entities
from opentaxii.utils import create_manager, create_services_from_config

from utils import get_service, prepare_headers, as_tm, persist_content
from utils import prepare_subscription_request as prepare_request

from fixtures import *

ASSIGNED_SERVICES = ['collection-management-A', 'poll-A']

@pytest.fixture
def manager():
    config = ServerConfig()
    config.update_persistence_api_config(
        'opentaxii.persistence.sqldb.SQLDatabaseAPI', {
            'db_connection' : 'sqlite://', # in-memory DB
            'create_tables' : True
    })
    config['services'].update(SERVICES)

    manager = create_manager(config)
    create_services_from_config(config, manager=manager)
    return manager


@pytest.fixture()
def server(manager):

    server = TAXIIServer(DOMAIN, manager=manager)

    for coll in COLLECTIONS_B:
        coll = manager.create_collection(coll)
        manager.attach_collection_to_services(coll.id, services_ids=ASSIGNED_SERVICES)

    return server


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_subscribe(server, version, https):

    service = get_service(server, 'collection-management-A')
    poll_service = get_service(server, 'poll-A')

    headers = prepare_headers(version, https)

    params = dict(
        response_type = RT_FULL,
        content_bindings = [CB_STIX_XML_111, CUSTOM_CONTENT_BINDING]
    )

    request = prepare_request(collection=COLLECTION_OPEN, action=ACT_SUBSCRIBE,
            version=version, params=params)

    response = service.process(headers, request)

    if version == 11:
        assert isinstance(response, as_tm(version).ManageCollectionSubscriptionResponse)
        assert response.collection_name == COLLECTION_OPEN
    else:
        assert isinstance(response, as_tm(version).ManageFeedSubscriptionResponse)
        assert response.feed_name == COLLECTION_OPEN

    assert response.message == SUBSCRIPTION_MESSAGE
    assert len(response.subscription_instances) == 1

    subs = response.subscription_instances[0]

    assert subs.subscription_id
    assert len(subs.poll_instances) == 2    # 1 poll service * 2 protocol bindings
    assert subs.poll_instances[0].poll_address == \
            poll_service.absolute_address(subs.poll_instances[0].poll_protocol)

    if version == 11:
        assert subs.status == SS_ACTIVE

        response_bindings = [b.binding_id for b in subs.subscription_parameters.content_bindings]

        assert response_bindings == params['content_bindings']
        assert subs.subscription_parameters.response_type == params['response_type']


@pytest.mark.parametrize("https", [True, False])
def test_subscribe_pause_resume(server, manager, https):

    version = 11

    service = get_service(server, 'collection-management-A')
    poll_service = get_service(server, 'poll-A')

    headers = prepare_headers(version, https)

    params = dict(
        response_type = RT_FULL,
        content_bindings = [CB_STIX_XML_111, CUSTOM_CONTENT_BINDING]
    )

    # Subscribing
    request = prepare_request(collection=COLLECTION_OPEN, action=ACT_SUBSCRIBE,
            version=version, params=params)

    response = service.process(headers, request)

    assert isinstance(response, as_tm(version).ManageCollectionSubscriptionResponse)
    assert response.collection_name == COLLECTION_OPEN

    assert len(response.subscription_instances) == 1

    subs = response.subscription_instances[0]

    assert subs.status == SS_ACTIVE
    assert manager.get_subscription(subs.subscription_id).status == SS_ACTIVE

    # Pausing
    request = prepare_request(collection=COLLECTION_OPEN, action=ACT_PAUSE,
            subscription_id=subs.subscription_id, version=version)

    response = service.process(headers, request)

    assert isinstance(response, as_tm(version).ManageCollectionSubscriptionResponse)
    assert response.collection_name == COLLECTION_OPEN

    assert len(response.subscription_instances) == 1

    subs = response.subscription_instances[0]

    assert subs.subscription_id
    assert subs.status == SS_PAUSED
    assert manager.get_subscription(subs.subscription_id).status == SS_PAUSED

    # Resume
    request = prepare_request(collection=COLLECTION_OPEN, action=ACT_RESUME,
            subscription_id=subs.subscription_id, version=version)

    response = service.process(headers, request)

    assert isinstance(response, as_tm(version).ManageCollectionSubscriptionResponse)
    assert response.collection_name == COLLECTION_OPEN

    assert len(response.subscription_instances) == 1

    subs = response.subscription_instances[0]

    assert subs.subscription_id
    assert subs.status == SS_ACTIVE
    assert manager.get_subscription(subs.subscription_id).status == SS_ACTIVE


@pytest.mark.parametrize("https", [True, False])
def test_pause_resume_wrong_id(server, https):

    version = 11

    service = get_service(server, 'collection-management-A')
    poll_service = get_service(server, 'poll-A')

    headers = prepare_headers(version, https)

    # Subscribing
    request = prepare_request(collection=COLLECTION_OPEN, action=ACT_SUBSCRIBE,
            version=version)

    response = service.process(headers, request)

    assert isinstance(response, as_tm(version).ManageCollectionSubscriptionResponse)
    assert response.collection_name == COLLECTION_OPEN

    assert len(response.subscription_instances) == 1
    subs = response.subscription_instances[0]

    assert subs.subscription_id
    assert subs.status == SS_ACTIVE

    # Pausing with wrong subscription ID
    with pytest.raises(exceptions.StatusMessageException):
        request = prepare_request(collection=COLLECTION_OPEN, action=ACT_PAUSE,
                subscription_id="RANDOM-WRONG-SUBSCRIPTION", version=version)
        response = service.process(headers, request)

    # Resuming with wrong subscription ID
    with pytest.raises(exceptions.StatusMessageException):
        request = prepare_request(collection=COLLECTION_OPEN, action=ACT_RESUME,
                subscription_id="RANDOM-WRONG-SUBSCRIPTION", version=version)
        response = service.process(headers, request)


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_unsubscribe(server, manager, version, https):

    service = get_service(server, 'collection-management-A')
    poll_service = get_service(server, 'poll-A')

    headers = prepare_headers(version, https)

    params = dict(
        response_type = RT_FULL,
        content_bindings = [CB_STIX_XML_111, CUSTOM_CONTENT_BINDING]
    )

    # Subscribing
    request = prepare_request(collection=COLLECTION_OPEN, action=ACT_SUBSCRIBE,
            version=version, params=params)

    response = service.process(headers, request)

    assert len(response.subscription_instances) == 1

    subs = response.subscription_instances[0]
    assert subs.subscription_id

    subscription_id = subs.subscription_id

    # Unsubscribing with invalid subscription ID should still return valid response
    INVALID_ID = "RANDOM-WRONG-SUBSCRIPTION"
    request = prepare_request(collection=COLLECTION_OPEN, action=ACT_UNSUBSCRIBE,
            subscription_id=INVALID_ID, version=version)
    response = service.process(headers, request)

    assert len(response.subscription_instances) == 1
    subs = response.subscription_instances[0]
    assert subs.subscription_id == INVALID_ID


    # Unsubscribing with valid subscription ID
    request = prepare_request(collection=COLLECTION_OPEN, action=ACT_UNSUBSCRIBE,
            subscription_id=subscription_id, version=version)
    response = service.process(headers, request)

    assert len(response.subscription_instances) == 1
    subs = response.subscription_instances[0]
    assert subs.subscription_id == subscription_id

    if version == 11:
        assert subs.status == SS_UNSUBSCRIBED

    assert manager.get_subscription(subscription_id).status == SS_UNSUBSCRIBED


# FIXME: add content_binding requested vs available tests

