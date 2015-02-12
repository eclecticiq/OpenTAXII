import pytest

from libtaxii import messages_10 as tm10
from libtaxii import messages_11 as tm11

from taxii_server.taxii import exceptions
from taxii_server.server import TAXIIServer
from taxii_server.options import ServerConfig

from taxii_server.persistence.sql import SQLDB
from taxii_server.persistence import DataStorage

from utils import get_service, prepare_headers, as_tm
from fixtures import *


def make_content(version, content_binding=CUSTOM_CONTENT_BINDING, content=CONTENT, subtype=None):
    if version == 10:
        return tm10.ContentBlock(content_binding, content)

    elif version == 11:
        content_block = tm11.ContentBlock(tm11.ContentBinding(content_binding), content)
        if subtype:
            content_block.content_binding.subtype_ids.append(subtype)

        return content_block
    else:
        raise ValueError('Unknown TAXII message version: %s' % version)



def make_inbox_message(version, blocks=None, dest_collection=None):

    if version == 10:
        inbox_message = tm10.InboxMessage(message_id=MESSAGE_ID, content_blocks=blocks)

    elif version == 11:
        inbox_message = tm11.InboxMessage(message_id=MESSAGE_ID, content_blocks=blocks)
        if dest_collection:
            inbox_message.destination_collection_names.append(dest_collection)
    else:
        raise ValueError('Unknown TAXII message version: %s' % version)

    return inbox_message


@pytest.fixture
def storage():
    db_connection = 'sqlite://' # in-memory DB
    storage = DataStorage(api=SQLDB(db_connection, create_tables=True))
    return storage


@pytest.fixture
def server(storage):
    
    config = ServerConfig(services_properties=SERVICES)

    server = TAXIIServer(DOMAIN, config.services, storage=storage)

    collections = map(storage.save_collection, COLLECTIONS)

    return server



@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_inbox_request_all_content(server, version, storage, https):

    inbox_a = get_service(server, 'inbox-A')

    headers = prepare_headers(version, https)

    blocks = [
        make_content(version, content_binding=CUSTOM_CONTENT_BINDING, subtype=CONTENT_SUBTYPE),
        make_content(version, content_binding=INVALID_CONTENT_BINDING)
    ]
    inbox_message = make_inbox_message(version, blocks=blocks)

    # "inbox-A" accepts all content
    response = inbox_a.process(headers, inbox_message)

    assert isinstance(response, as_tm(version).StatusMessage)

    assert response.status_type == ST_SUCCESS
    assert response.in_response_to == MESSAGE_ID

    blocks = storage.get_content_blocks()
    assert len(blocks) == len(blocks)


@pytest.mark.parametrize("https", [True, False])
def test_inbox_request_destination_collection(server, https):
    version = 11

    inbox_message = make_inbox_message(version, blocks=[make_content(version)], dest_collection=None)
    headers = prepare_headers(version, https)

    inbox = get_service(server, 'inbox-A')
    # destination collection is not required for inbox-A
    response = inbox.process(headers, inbox_message)

    assert isinstance(response, as_tm(version).StatusMessage)
    assert response.status_type == ST_SUCCESS

    inbox = get_service(server, 'inbox-B')
    # destination collection is required for inbox-B
    with pytest.raises(exceptions.StatusMessageException):
        response = inbox.process(headers, inbox_message)


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_inbox_request_inbox_valid_content_binding(server, storage, version, https):

    inbox = get_service(server, 'inbox-B')

    blocks = [
        make_content(version, content_binding=CUSTOM_CONTENT_BINDING, subtype=CONTENT_SUBTYPE),
        make_content(version, content_binding=CB_STIX_XML_111)
    ]

    inbox_message = make_inbox_message(version, dest_collection=COLLECTION_OPEN, blocks=blocks)
    headers = prepare_headers(version, https)

    response = inbox.process(headers, inbox_message)

    assert isinstance(response, as_tm(version).StatusMessage)
    assert response.status_type == ST_SUCCESS
    assert response.in_response_to == MESSAGE_ID

    blocks = storage.get_content_blocks()
    assert len(blocks) == len(blocks)


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_inbox_request_inbox_invalid_inbox_content_binding(server, storage, version, https):

    inbox = get_service(server, 'inbox-B')

    content = make_content(version, content_binding=INVALID_CONTENT_BINDING)
    inbox_message = make_inbox_message(version, dest_collection=COLLECTION_OPEN, blocks=[content])

    headers = prepare_headers(version, https)

    response = inbox.process(headers, inbox_message)

    assert isinstance(response, as_tm(version).StatusMessage)
    assert response.status_type == ST_SUCCESS
    assert response.in_response_to == MESSAGE_ID

    blocks = storage.get_content_blocks()

    # Content blocks with invalid content should be ignored
    assert len(blocks) == 0


@pytest.mark.parametrize("https", [True, False])
@pytest.mark.parametrize("version", [11, 10])
def test_inbox_request_collection_content_bindings_filtering(server, storage, version, https):

    inbox = get_service(server, 'inbox-B')
    headers = prepare_headers(version, https)

    blocks = [
        make_content(version, content_binding=CUSTOM_CONTENT_BINDING),
        make_content(version, content_binding=INVALID_CONTENT_BINDING),
    ]

    inbox_message = make_inbox_message(version, dest_collection=COLLECTION_ONLY_STIX, blocks=blocks)

    response = inbox.process(headers, inbox_message)

    assert isinstance(response, as_tm(version).StatusMessage)
    assert response.status_type == ST_SUCCESS
    assert response.in_response_to == MESSAGE_ID

    blocks = storage.get_content_blocks()

    # Content blocks with invalid content should be ignored
    assert len(blocks) == 1


