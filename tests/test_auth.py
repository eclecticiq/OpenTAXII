import json
import pytest

import base64

from libtaxii import messages_10 as tm10
from libtaxii import messages_11 as tm11
from libtaxii.constants import (
    ST_UNAUTHORIZED, ST_BAD_MESSAGE, CB_STIX_XML_111, RT_FULL)
from opentaxii.taxii.http import HTTP_AUTHORIZATION
from opentaxii.utils import sync_conf_dict_into_db

from utils import prepare_headers, is_headers_valid, as_tm
from fixtures import VID_TAXII_HTTP_10


INBOX_OPEN = dict(
    id='inbox-A',
    type='inbox',
    description='inboxA description',
    address='/path/inbox',
    destination_collection_required=True,
    authentication_required=False)

INBOX_CLOSED = dict(
    id='inbox-A',
    type='inbox',
    description='inboxA description',
    address='/path/inbox',
    destination_collection_required=True,
    authentication_required=True)

DISCOVERY = dict(
    id='discovery-A',
    type='discovery',
    description='discoveryA description',
    address='/path/discovery',
    advertised_services=['inbox-A', 'poll-A'],
    protocol_bindings=[VID_TAXII_HTTP_10],
    authentication_required=True)

POLL_CLOSED = dict(
    id='poll-A',
    type='poll',
    description='Poll service description',
    address='/path/poll-a',
    protocol_bindings=[VID_TAXII_HTTP_10],
    authentication_required=True,
    max_result_size=100,
    max_result_count=10)

POLL_OPEN = dict(
    id='poll-B',
    type='poll',
    description='Poll service description',
    address='/path/poll-b',
    protocol_bindings=[VID_TAXII_HTTP_10],
    authentication_required=False,  # <- open for all
    max_result_size=100,
    max_result_count=10)

CONTENT = 'inbox-message-content'

COLLECTIONS = [
    {'name': 'collection-1',
     'available': True,
     'accept_all_content': True,
     'type': 'DATA_FEED',
     'service_ids': ['discovery-A', 'inbox-A', 'poll-A', 'poll-B']},
    {'name': 'collection-2',
     'available': True,
     'accept_all_content': True,
     'type': 'DATA_FEED',
     'service_ids': ['discovery-A', 'inbox-A', 'poll-A', 'poll-B']}]

USERNAME = 'some-username'
PASSWORD = 'some-password'

ACCOUNTS = [
    {'username': 'johnny',
     'password': 'johnny',
     'permissions': {
         'collection-1': 'read',
         'collection-2': 'modify'}},
    {'username': 'billy',
     'password': 'billy',
     'permissions': {
         'collection-1': 'modify'}},
    {'username': 'wally',
     'password': 'wally',
     'is_admin': True},
    {'username': USERNAME,
     'password': PASSWORD}]

MESSAGE_ID = '123'

AUTH_PATH = '/management/auth'


@pytest.fixture(autouse=True)
def auth_fixtures(server):
    sync_conf_dict_into_db(
        server,
        config={
            'services': [
                INBOX_OPEN, INBOX_CLOSED,
                DISCOVERY, POLL_OPEN, POLL_CLOSED],
            'collections': COLLECTIONS,
            'accounts': ACCOUNTS})

    assert len(server.persistence.get_services()) == 4
    assert len(server.persistence.get_collections()) == len(COLLECTIONS)


@pytest.fixture()
def test_account(server):
    from opentaxii.entities import Account
    account = Account(id=None, username=USERNAME, permissions={})
    server.auth.update_account(account, PASSWORD)


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_unauthorized_request(app, client, version, https):
    base_url = '%s://localhost' % ('https' if https else 'http')
    response = client.post(
        INBOX_OPEN['address'],
        data='invalid-body',
        headers=prepare_headers(version, https),
        base_url=base_url)

    assert response.status_code == 200
    assert is_headers_valid(response.headers, version, https)

    message = as_tm(version).get_message_from_xml(response.data)
    assert message.status_type == ST_UNAUTHORIZED

    from opentaxii import context
    assert not hasattr(context, 'account')


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_get_token(client, version, https):
    base_url = '%s://localhost' % ('https' if https else 'http')
    # Invalid credentials
    response = client.post(
        AUTH_PATH,
        data={'username': 'dummy', 'password': 'wrong'},
        base_url=base_url)
    assert response.status_code == 401

    # Invalid auth data
    response = client.post(
        AUTH_PATH,
        data={'other': 'somethind'},
        base_url=base_url)
    assert response.status_code == 400

    # Valid credentials as form data
    response = client.post(
        AUTH_PATH,
        data={'username': USERNAME, 'password': PASSWORD},
        base_url=base_url)

    assert response.status_code == 200

    data = json.loads(response.get_data(as_text=True))
    assert data.get('token')

    # Valid credentials as JSON blob
    response = client.post(
        AUTH_PATH,
        data=json.dumps({'username': USERNAME, 'password': PASSWORD}),
        base_url=base_url,
        content_type='application/json')

    assert response.status_code == 200

    data = json.loads(response.get_data(as_text=True))
    assert data.get('token')


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_get_token_and_send_request(client, version, https):

    base_url = '%s://localhost' % ('https' if https else 'http')

    # Get valid token
    response = client.post(
        AUTH_PATH,
        data={'username': USERNAME, 'password': PASSWORD},
        base_url=base_url)

    assert response.status_code == 200

    data = json.loads(response.get_data(as_text=True))
    token = data.get('token')

    assert token

    headers = prepare_headers(version, https)
    headers[HTTP_AUTHORIZATION] = 'Bearer %s' % token

    # Get correct response for invalid body
    response = client.post(
        INBOX_OPEN['address'],
        data='invalid-body',
        headers=headers,
        base_url=base_url)

    assert response.status_code == 200
    assert is_headers_valid(response.headers, version, https)

    message = as_tm(version).get_message_from_xml(response.data)
    assert message.status_type == ST_BAD_MESSAGE

    request = as_tm(version).DiscoveryRequest(message_id=MESSAGE_ID)
    headers = prepare_headers(version, https)
    headers[HTTP_AUTHORIZATION] = 'Bearer %s' % token

    # Get correct response for valid request
    response = client.post(
        DISCOVERY['address'],
        data=request.to_xml(),
        headers=headers,
        base_url=base_url)

    assert response.status_code == 200
    assert is_headers_valid(response.headers, version=version, https=https)

    message = as_tm(version).get_message_from_xml(response.data)

    assert isinstance(message, as_tm(version).DiscoveryResponse)

    from opentaxii import context
    assert not hasattr(context, 'account')


def basic_auth_token(username, password):
    return base64.b64encode(
        '{}:{}'.format(username, password).encode('utf-8'))


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_request_with_basic_auth(client, version, https):

    base_url = '%s://localhost' % ('https' if https else 'http')
    basic_auth_header = 'Basic {}'.format(
        basic_auth_token(USERNAME, PASSWORD).decode('utf-8'))

    headers = prepare_headers(version, https)
    headers[HTTP_AUTHORIZATION] = basic_auth_header

    # Get correct response for invalid body
    response = client.post(
        INBOX_OPEN['address'],
        data='invalid-body',
        headers=headers,
        base_url=base_url)

    assert response.status_code == 200
    assert is_headers_valid(response.headers, version, https)

    message = as_tm(version).get_message_from_xml(response.data)
    assert message.status_type == ST_BAD_MESSAGE

    request = as_tm(version).DiscoveryRequest(message_id=MESSAGE_ID)
    headers = prepare_headers(version, https)
    headers[HTTP_AUTHORIZATION] = basic_auth_header

    # Get correct response for valid request
    response = client.post(
        DISCOVERY['address'],
        data=request.to_xml(),
        headers=headers,
        base_url=base_url
    )

    assert response.status_code == 200
    assert is_headers_valid(response.headers, version=version, https=https)

    message = as_tm(version).get_message_from_xml(response.data)

    assert isinstance(message, as_tm(version).DiscoveryResponse)

    from opentaxii import context
    assert not hasattr(context, 'account')


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_invalid_basic_auth_request(client, version, https):

    base_url = '%s://localhost' % ('https' if https else 'http')

    headers = prepare_headers(version, https)
    headers[HTTP_AUTHORIZATION] = 'Basic somevalue'

    request = as_tm(version).DiscoveryRequest(message_id=MESSAGE_ID)
    response = client.post(
        DISCOVERY['address'],
        data=request.to_xml(),
        headers=headers,
        base_url=base_url)

    assert response.status_code == 200
    assert is_headers_valid(response.headers, version, https)

    message = as_tm(version).get_message_from_xml(response.data)
    assert message.status_type == ST_UNAUTHORIZED


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_invalid_auth_header_request(client, version, https):

    base_url = '%s://localhost' % ('https' if https else 'http')

    headers = prepare_headers(version, https)

    basic_auth_header = 'Foo {}'.format(basic_auth_token(USERNAME, PASSWORD))
    headers[HTTP_AUTHORIZATION] = basic_auth_header

    request = as_tm(version).DiscoveryRequest(message_id=MESSAGE_ID)
    response = client.post(
        DISCOVERY['address'],
        data=request.to_xml(),
        headers=headers,
        base_url=base_url)

    assert response.status_code == 200
    assert is_headers_valid(response.headers, version, https)

    message = as_tm(version).get_message_from_xml(response.data)
    assert message.status_type == ST_UNAUTHORIZED


def prepare_url_headers(version, https, username, password):
    base_url = '%s://localhost' % ('https' if https else 'http')
    headers = prepare_headers(version, https)
    basic_auth_header = 'Basic {}'.format(
        basic_auth_token(username, password).decode('utf-8'))
    headers[HTTP_AUTHORIZATION] = basic_auth_header
    return base_url, headers


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_collection_access_private_poll(client, version, https):

    # POLL_CLOSED collection allowed read access
    url, headers = prepare_url_headers(version, https, 'johnny', 'johnny')
    request = prepare_poll_request(
        'collection-1', version, bindings=[CB_STIX_XML_111])

    response = client.post(
        POLL_CLOSED['address'],
        data=request.to_xml(),
        headers=headers,
        base_url=url)
    assert response.status_code == 200
    assert is_headers_valid(response.headers, version, https)
    message = as_tm(version).get_message_from_xml(response.data)
    assert message.message_type == 'Poll_Response'

    # POLL_CLOSED collection disallowed read access
    url, headers = prepare_url_headers(version, https, 'billy', 'billy')
    request = prepare_poll_request(
        'collection-2', version, bindings=[CB_STIX_XML_111])

    response = client.post(
        POLL_CLOSED['address'],
        data=request.to_xml(),
        headers=headers,
        base_url=url)
    assert response.status_code == 200
    assert is_headers_valid(response.headers, version, https)
    message = as_tm(version).get_message_from_xml(response.data)
    assert message.status_type == 'NOT_FOUND'

    # POLL_CLOSED collection admin access
    url, headers = prepare_url_headers(version, https, 'wally', 'wally')
    request = prepare_poll_request(
        'collection-2', version, bindings=[CB_STIX_XML_111])

    response = client.post(
        POLL_CLOSED['address'],
        data=request.to_xml(),
        headers=headers,
        base_url=url)
    assert response.status_code == 200
    assert is_headers_valid(response.headers, version, https)
    message = as_tm(version).get_message_from_xml(response.data)
    assert message.message_type == 'Poll_Response'


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_collection_access_private_inbox(client, version, https):
    # INBOX read-only collection access
    url, headers = prepare_url_headers(version, https, 'johnny', 'johnny')
    request = prepare_inbox_message(
        version,
        dest_collection='collection-1',
        blocks=[make_inbox_content(version)])

    response = client.post(
        INBOX_CLOSED['address'],
        data=request.to_xml(),
        headers=headers,
        base_url=url)
    assert response.status_code == 200
    assert is_headers_valid(response.headers, version, https)
    message = as_tm(version).get_message_from_xml(response.data)
    assert message.message_type == 'Status_Message'

    if version == 11:
        assert message.status_type == 'UNAUTHORIZED'
        assert (
            message.message ==
            'User can not write to collection collection-1')
    else:
        # Because in TAXII 1.0 destination collection can not be specified
        # so it impossible to verify access
        assert message.status_type == 'SUCCESS'

    # INBOX modify collection access
    request = prepare_inbox_message(
        version,
        dest_collection='collection-2',
        blocks=[make_inbox_content(version)])

    response = client.post(
        INBOX_CLOSED['address'],
        data=request.to_xml(),
        headers=headers,
        base_url=url)
    assert response.status_code == 200
    assert is_headers_valid(response.headers, version, https)
    message = as_tm(version).get_message_from_xml(response.data)
    assert message.message_type == 'Status_Message'
    assert message.status_type == 'SUCCESS'

    # INBOX modify collection access
    url, headers = prepare_url_headers(version, https, 'wally', 'wally')
    request = prepare_inbox_message(
        version,
        dest_collection='collection-2',
        blocks=[make_inbox_content(version)])

    response = client.post(
        INBOX_CLOSED['address'],
        data=request.to_xml(),
        headers=headers,
        base_url=url)
    assert response.status_code == 200
    assert is_headers_valid(response.headers, version, https)
    message = as_tm(version).get_message_from_xml(response.data)
    assert message.message_type == 'Status_Message'
    assert message.status_type == 'SUCCESS'


def prepare_poll_request(
        collection_name, version, bindings=[], subscription_id=None):

    if version == 11:
        content_bindings = [tm11.ContentBinding(b) for b in bindings]
        if subscription_id:
            poll_parameters = None
        else:
            poll_parameters = tm11.PollParameters(
                response_type=RT_FULL,
                content_bindings=content_bindings)
        return tm11.PollRequest(
            message_id=MESSAGE_ID,
            collection_name=collection_name,
            subscription_id=subscription_id,
            poll_parameters=poll_parameters)
    elif version == 10:
        content_bindings = bindings
        return tm10.PollRequest(
            message_id=MESSAGE_ID,
            feed_name=collection_name,
            content_bindings=content_bindings,
            subscription_id=subscription_id)


def make_inbox_content(
        version, content_binding=CB_STIX_XML_111, content=CONTENT):
    if version == 10:
        return tm10.ContentBlock(content_binding, content)

    elif version == 11:
        return tm11.ContentBlock(
            tm11.ContentBinding(content_binding), content)
    else:
        raise ValueError('Unknown TAXII message version: %s' % version)


def prepare_inbox_message(version, blocks=None, dest_collection=None):
    if version == 10:
        inbox_message = tm10.InboxMessage(
            message_id=MESSAGE_ID, content_blocks=blocks)
    elif version == 11:
        inbox_message = tm11.InboxMessage(
            message_id=MESSAGE_ID, content_blocks=blocks)
        if dest_collection:
            inbox_message.destination_collection_names.append(dest_collection)
    else:
        raise ValueError('Unknown TAXII message version: %s' % version)
    return inbox_message
