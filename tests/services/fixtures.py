from libtaxii.constants import *

from opentaxii.taxii import entities

PROTOCOL_BINDINGS = [VID_TAXII_HTTP_10, VID_TAXII_HTTPS_10]

CUSTOM_CONTENT_BINDING = 'custom:content:binding'
INVALID_CONTENT_BINDING = 'invalid:content:binding'

INBOX_A = dict(
    type = 'inbox',
    description = 'inbox-A description',
    destination_collection_required = False,
    address = '/relative/path/inbox-a',
    accept_all_content = True,
    protocol_bindings = PROTOCOL_BINDINGS
)

INBOX_B = dict(
    type = 'inbox',
    description = 'inbox-B description',
    destination_collection_required = 'yes',
    address = '/relative/path/inbox-b',
    supported_content = [CB_STIX_XML_111, CUSTOM_CONTENT_BINDING],
    protocol_bindings = PROTOCOL_BINDINGS
)

DISCOVERY_A = dict(
    type = 'discovery',
    description = 'discovery-A description',
    address = '/relative/path/discovery-a',
    advertised_services = ['inbox-A', 'inbox-B', 'discovery-A', 'discovery-B',
        'collection-management-A', 'poll-A'],
    protocol_bindings = PROTOCOL_BINDINGS
)

DISCOVERY_B = dict(
    type = 'discovery',
    description = 'External discovery-B service',
    address = 'http://something.com/absolute/path/discovery-b',
    protocol_bindings = [VID_TAXII_HTTP_10]
)

SUBSCRIPTION_MESSAGE = 'message about subscription'

COLLECTION_MANAGEMENT = dict(
    type = 'collection_management',
    description = 'Collection management description',
    address = '/relative/path/collection-management',
    protocol_bindings = PROTOCOL_BINDINGS,
    subscription_message = SUBSCRIPTION_MESSAGE
)

POLL_RESULT_SIZE = 20
POLL_MAX_COUNT = 15 

POLL = dict(
    type = 'poll',
    description = 'Poll service description',
    address = '/relative/path/poll',
    protocol_bindings = PROTOCOL_BINDINGS,
    max_result_size = POLL_RESULT_SIZE,
    max_result_count = POLL_MAX_COUNT 
)

DOMAIN = 'www.some-example.com'

INTERNAL_SERVICES = [INBOX_A, INBOX_B, DISCOVERY_A, COLLECTION_MANAGEMENT, POLL]
SERVICES = {
    'inbox-A' : INBOX_A,
    'inbox-B' : INBOX_B,
    'discovery-A' : DISCOVERY_A,
    'discovery-B' : DISCOVERY_B,
    'collection-management-A' : COLLECTION_MANAGEMENT,
    'poll-A' : POLL
}

INSTANCES_CONFIGURED = sum(len(s['protocol_bindings']) for s in SERVICES.values())

MESSAGE_ID = '123'
CONTENT = 'some-content'

CONTENT_BINDINGS_ONLY_STIX = [CB_STIX_XML_111]
CONTENT_BINDINGS_STIX_AND_CUSTOM = CONTENT_BINDINGS_ONLY_STIX + [CUSTOM_CONTENT_BINDING]
CONTENT_BINDING_SUBTYPE = 'custom-subtype'

MESSAGE = 'test-message'


COLLECTION_OPEN = "collection_open"
COLLECTION_ONLY_STIX = "collection_only_stix"
COLLECTION_STIX_AND_CUSTOM = "collection_stix_and_custom"
COLLECTION_DISABLED = "collection_disabled"


COLLECTIONS_A = map(lambda x: entities.CollectionEntity(**x), [
    dict(name=COLLECTION_OPEN, available=True, accept_all_content=True),
])

COLLECTIONS_B = map(lambda x: entities.CollectionEntity(**x), [

    dict(name=COLLECTION_OPEN, available=True, accept_all_content=True,
        type=entities.CollectionEntity.TYPE_SET),

    dict(name=COLLECTION_ONLY_STIX, available=True, accept_all_content=False,
        supported_content=CONTENT_BINDINGS_ONLY_STIX),

    dict(name=COLLECTION_STIX_AND_CUSTOM, available=True, accept_all_content=False,
        supported_content=CONTENT_BINDINGS_STIX_AND_CUSTOM),

    dict(name=COLLECTION_DISABLED, available=False)
])

