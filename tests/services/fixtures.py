from libtaxii.constants import *

from taxii_server.taxii.bindings import ContentBinding
from taxii_server.taxii.entities import DataCollectionEntity

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
    advertised_services = ['inbox-A', 'inbox-B', 'discovery-A', 'discovery-B'],
    protocol_bindings = PROTOCOL_BINDINGS
)

DISCOVERY_B = dict(
    type = 'discovery',
    description = 'External discovery-B service',
    address = 'http://something.com/absolute/path/discovery-b',
    protocol_bindings = PROTOCOL_BINDINGS
)

DOMAIN = 'www.some-example.com'

INTERNAL_SERVICES = [INBOX_A, INBOX_B, DISCOVERY_A]
SERVICES = {
    'inbox-A' : INBOX_A,
    'inbox-B' : INBOX_B,
    'discovery-A' : DISCOVERY_A,
    'discovery-B' : DISCOVERY_B
}

INSTANCES_CONFIGURED = sum(len(s['protocol_bindings']) for s in SERVICES.values())

MESSAGE_ID = '123'
CONTENT = 'some-content'
CONTENT_SUBTYPE = 'custom-subtype'

CONTENT_BINDINGS_ONLY_STIX = [ContentBinding(binding=CB_STIX_XML_111, subtypes=None)]
CONTENT_BINDINGS_STIX_AND_CUSTOM = CONTENT_BINDINGS_ONLY_STIX + [ContentBinding(binding=CUSTOM_CONTENT_BINDING, subtypes=None)]


COLLECTION_OPEN = "collection_open"
COLLECTION_ONLY_STIX = "collection_only_stix"
COLLECTION_STIX_AND_CUSTOM = "collection_stix_and_custom"
COLLECTION_DISABLED = "collection_disabled"


COLLECTIONS = map(lambda x: DataCollectionEntity.create(**x), [
    dict(inbox_id='inbox-A', name=COLLECTION_OPEN, enabled=True, accept_all_content=True),

    dict(inbox_id='inbox-B', name=COLLECTION_OPEN, enabled=True, accept_all_content=True),

    dict(inbox_id='inbox-B', name=COLLECTION_ONLY_STIX, enabled=True, accept_all_content=False,
        supported_content=CONTENT_BINDINGS_ONLY_STIX),

    dict(inbox_id='inbox-B', name=COLLECTION_STIX_AND_CUSTOM, enabled=True, accept_all_content=False,
        supported_content=CONTENT_BINDINGS_STIX_AND_CUSTOM),

    dict(inbox_id='inbox-B', name=COLLECTION_DISABLED, enabled=False)
])

