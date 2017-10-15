import pytest

from libtaxii.constants import (
    RT_FULL, CB_STIX_XML_111, ACT_PAUSE, ACT_RESUME, ACT_UNSUBSCRIBE,
    ACT_SUBSCRIBE, SS_ACTIVE, SS_PAUSED, SS_UNSUBSCRIBED)

from opentaxii.taxii import exceptions

from utils import (
    prepare_headers, as_tm,
    prepare_subscription_request as prepare_request)

from fixtures import (
    CUSTOM_CONTENT_BINDING, COLLECTION_OPEN, SUBSCRIPTION_MESSAGE,
    COLLECTIONS_B)

ASSIGNED_SERVICES = ['collection-management-A', 'poll-A']


@pytest.fixture(autouse=True)
def prepare_server(server, services):
    for coll in COLLECTIONS_B:
        coll = server.persistence.create_collection(coll)
        server.persistence.set_collection_services(
            coll.id, service_ids=ASSIGNED_SERVICES)
    return server


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_subscribe(server, version, https):

    service = server.get_service('collection-management-A')
    poll_service = server.get_service('poll-A')

    headers = prepare_headers(version, https)

    params = dict(
        response_type=RT_FULL,
        content_bindings=[CB_STIX_XML_111, CUSTOM_CONTENT_BINDING]
    )

    request = prepare_request(
        collection=COLLECTION_OPEN, action=ACT_SUBSCRIBE,
        version=version, params=params)

    response = service.process(headers, request)

    if version == 11:
        assert isinstance(
            response,
            as_tm(version).ManageCollectionSubscriptionResponse)
        assert response.collection_name == COLLECTION_OPEN
    else:
        assert isinstance(
            response,
            as_tm(version).ManageFeedSubscriptionResponse)
        assert response.feed_name == COLLECTION_OPEN

    assert response.message == SUBSCRIPTION_MESSAGE
    assert len(response.subscription_instances) == 1

    subs = response.subscription_instances[0]

    assert subs.subscription_id

    # 1 poll service * 2 protocol bindings
    assert len(subs.poll_instances) == 2
    assert (
        subs.poll_instances[0].poll_address ==
        poll_service.get_absolute_address(
            subs.poll_instances[0].poll_protocol))

    if version == 11:
        assert subs.status == SS_ACTIVE

        response_bindings = [
            b.binding_id
            for b in subs.subscription_parameters.content_bindings]

        assert response_bindings == params['content_bindings']
        assert (
            subs.subscription_parameters.response_type ==
            params['response_type'])


@pytest.mark.parametrize("https", [True, False])
def test_subscribe_pause_resume(server, https):

    version = 11

    service = server.get_service('collection-management-A')

    headers = prepare_headers(version, https)

    params = dict(
        response_type=RT_FULL,
        content_bindings=[CB_STIX_XML_111, CUSTOM_CONTENT_BINDING]
    )

    # Subscribing
    request = prepare_request(
        collection=COLLECTION_OPEN, action=ACT_SUBSCRIBE,
        version=version, params=params)

    response = service.process(headers, request)

    assert isinstance(
        response,
        as_tm(version).ManageCollectionSubscriptionResponse)
    assert response.collection_name == COLLECTION_OPEN

    assert len(response.subscription_instances) == 1

    subs = response.subscription_instances[0]

    assert subs.status == SS_ACTIVE
    assert (
        server.persistence.get_subscription(subs.subscription_id).status ==
        SS_ACTIVE)

    # Pausing
    request = prepare_request(
        collection=COLLECTION_OPEN, action=ACT_PAUSE,
        subscription_id=subs.subscription_id, version=version)

    response = service.process(headers, request)

    assert isinstance(
        response,
        as_tm(version).ManageCollectionSubscriptionResponse)
    assert response.collection_name == COLLECTION_OPEN

    assert len(response.subscription_instances) == 1

    subs = response.subscription_instances[0]

    assert subs.subscription_id
    assert subs.status == SS_PAUSED
    assert (
        server.persistence.get_subscription(subs.subscription_id).status ==
        SS_PAUSED)

    # Resume
    request = prepare_request(
        collection=COLLECTION_OPEN, action=ACT_RESUME,
        subscription_id=subs.subscription_id, version=version)

    response = service.process(headers, request)

    assert isinstance(
        response,
        as_tm(version).ManageCollectionSubscriptionResponse)
    assert response.collection_name == COLLECTION_OPEN

    assert len(response.subscription_instances) == 1

    subs = response.subscription_instances[0]

    assert subs.subscription_id
    assert subs.status == SS_ACTIVE
    assert (
        server.persistence.get_subscription(subs.subscription_id).status ==
        SS_ACTIVE)


@pytest.mark.parametrize("https", [True, False])
def test_pause_resume_wrong_id(server, https):

    version = 11
    service = server.get_service('collection-management-A')

    headers = prepare_headers(version, https)

    # Subscribing
    request = prepare_request(
        collection=COLLECTION_OPEN, action=ACT_SUBSCRIBE,
        version=version)

    response = service.process(headers, request)

    assert isinstance(
        response, as_tm(version).ManageCollectionSubscriptionResponse)
    assert response.collection_name == COLLECTION_OPEN

    assert len(response.subscription_instances) == 1
    subs = response.subscription_instances[0]

    assert subs.subscription_id
    assert subs.status == SS_ACTIVE

    # Pausing with wrong subscription ID
    with pytest.raises(exceptions.StatusMessageException):
        request = prepare_request(
            collection=COLLECTION_OPEN, action=ACT_PAUSE,
            subscription_id="RANDOM-WRONG-SUBSCRIPTION", version=version)
        response = service.process(headers, request)

    # Resuming with wrong subscription ID
    with pytest.raises(exceptions.StatusMessageException):
        request = prepare_request(
            collection=COLLECTION_OPEN, action=ACT_RESUME,
            subscription_id="RANDOM-WRONG-SUBSCRIPTION", version=version)
        response = service.process(headers, request)


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_unsubscribe(server, version, https):

    service = server.get_service('collection-management-A')
    headers = prepare_headers(version, https)

    params = dict(
        response_type=RT_FULL,
        content_bindings=[CB_STIX_XML_111, CUSTOM_CONTENT_BINDING]
    )

    # Subscribing
    request = prepare_request(
        collection=COLLECTION_OPEN, action=ACT_SUBSCRIBE,
        version=version, params=params)

    response = service.process(headers, request)

    assert len(response.subscription_instances) == 1

    subs = response.subscription_instances[0]
    assert subs.subscription_id

    subscription_id = subs.subscription_id

    # Unsubscribing with invalid subscription ID should still
    # return valid response
    INVALID_ID = "RANDOM-WRONG-SUBSCRIPTION"
    request = prepare_request(
        collection=COLLECTION_OPEN, action=ACT_UNSUBSCRIBE,
        subscription_id=INVALID_ID, version=version)
    response = service.process(headers, request)

    assert len(response.subscription_instances) == 1
    subs = response.subscription_instances[0]
    assert subs.subscription_id == INVALID_ID

    # Unsubscribing with valid subscription ID
    request = prepare_request(
        collection=COLLECTION_OPEN, action=ACT_UNSUBSCRIBE,
        subscription_id=subscription_id, version=version)
    response = service.process(headers, request)

    assert len(response.subscription_instances) == 1
    subs = response.subscription_instances[0]
    assert subs.subscription_id == subscription_id

    if version == 11:
        assert subs.status == SS_UNSUBSCRIBED

    assert (
        server.persistence.get_subscription(subscription_id).status ==
        SS_UNSUBSCRIBED)
