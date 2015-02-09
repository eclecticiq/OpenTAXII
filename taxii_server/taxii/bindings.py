
import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.validation import SchemaValidator
from libtaxii.constants import *

from collections import namedtuple

ContentBinding = namedtuple("ContentBinding", "binding subtypes")
ValidatorAndParser = namedtuple('ValidatorAndParser', ['validator', 'parser'])


CONTENT_BINDINGS = [
    ContentBinding(binding=CB_STIX_XML_10, subtypes=None),
    ContentBinding(binding=CB_STIX_XML_101, subtypes=None),
    ContentBinding(binding=CB_STIX_XML_11, subtypes=None),
    ContentBinding(binding=CB_STIX_XML_111, subtypes=None),
    #ContentBinding(main=CB_CAP_11, subtype=None),
]

ALL_PROTOCOL_BINDINGS = [
    VID_TAXII_HTTP_10, 
    VID_TAXII_HTTPS_10
]

PROTOCOL_TO_SCHEME = {
    VID_TAXII_HTTP_10 : 'http://',
    VID_TAXII_HTTPS_10 : 'https://'
}

MESSAGE_BINDINGS = [
    VID_TAXII_XML_10,
    VID_TAXII_XML_11
]

SERVICE_BINDINGS = [
    VID_TAXII_SERVICES_10,
    VID_TAXII_SERVICES_11
]

MESSAGE_VALIDATOR_PARSER = {
    VID_TAXII_XML_10: ValidatorAndParser(SchemaValidator(SchemaValidator.TAXII_10_SCHEMA), tm10.get_message_from_xml),
    VID_TAXII_XML_11: ValidatorAndParser(SchemaValidator(SchemaValidator.TAXII_11_SCHEMA), tm11.get_message_from_xml)
}

