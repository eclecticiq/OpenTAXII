from datetime import datetime
from collections import namedtuple

import pytz
import structlog
import six
import sdv

from lxml import etree
from libtaxii.common import set_xml_parser
from libtaxii.constants import (
    CB_STIX_XML_10, CB_STIX_XML_101, CB_STIX_XML_11, CB_STIX_XML_111, CB_STIX_XML_12
)

from .exceptions import BadMessageStatus
from .bindings import MESSAGE_VALIDATOR_PARSER

log = structlog.getLogger(__name__)


def get_utc_now():
    return datetime.utcnow().replace(tzinfo=pytz.UTC)


def is_content_supported(supported_bindings, content_binding, version=None):

    if not hasattr(content_binding, u'binding_id') or version == 10:
        binding_id = content_binding
        subtype = None
    else:
        binding_id = content_binding.binding_id

        # FIXME: may be not the best option
        subtype = (
            content_binding.subtype_ids[0] if content_binding.subtype_ids
            else None)

    matches = [
        ((supported.binding == binding_id) and
         (not supported.subtypes or subtype in supported.subtypes))
        for supported in supported_bindings
    ]

    return any(matches)

def verify_content_is_valid(content, content_binding, taxii_message_id):

    # Validate that the STIX content is actually STIX content with the STIX Validator
    verify_results = namedtuple(u'VerifyResults', u'is_valid message')

    # Handle whatever sort of bytes or strings we get
    # and put it in a StringIO so that the Stix-validator will process it correctly
    if isinstance(content, six.BytesIO):
        content_to_validate = six.StringIO(content.decode())
    elif isinstance(content, bytes):
        content_to_validate = six.StringIO(content.decode())
    else:
        content_to_validate = six.StringIO(content)

    if not isinstance(content_binding, str): 
        content_binding = str(content_binding.to_text())

    try:
        # Run the STIX data validator with the correct content binding
        # Eliminates the chance of a client sending the wrong STIX file with the
        # wrong content_binding.
        if content_binding == CB_STIX_XML_10:
            results = sdv.validate_xml(content_to_validate, u'1.0')
        elif content_binding == CB_STIX_XML_101:
            results = sdv.validate_xml(content_to_validate, u'1.0.1')
        elif content_binding == CB_STIX_XML_11:
            results = sdv.validate_xml(content_to_validate, u'1.1')
        elif content_binding == CB_STIX_XML_111:
            results = sdv.validate_xml(content_to_validate, u'1.1.1')
        elif content_binding == CB_STIX_XML_12:
            results = sdv.validate_xml(content_to_validate, u'1.2')
        else:
            # this is not a content type we can validate
            # it might be a custom URN, so we need to just let it through without validation
            return verify_results(is_valid=True,
                 message=  "The STIX content in the content block is valid ({})."
                 .format(content_binding)
            )
        # Test the results of the validator to make sure the schema is valid
        if not results.is_valid:
            return verify_results(is_valid=False,
                         message= "The TAXII message {} contains invalid STIX {} content in one of the content blocks (incorrect content binding supplied?)."
                         .format(taxii_message_id,content_binding)
            )
            
    except Exception as ve:
        return verify_results(is_valid=False,
                     message= "The TAXII message {} contains invalid STIX {} content in one of the content blocks (incorrect content binding supplied?)."
                     .format(taxii_message_id,content_binding)
        )
        
    return verify_results(is_valid=True,
                 message=  "The STIX content in the content block is valid ({})."
                 .format(content_binding)
    )


def parse_message(content_type, body, do_validate=True):

    validator_parser = MESSAGE_VALIDATOR_PARSER[content_type]

    if do_validate:
        try:
            result = validator_parser.validator.validate_string(body)
            if not result.valid:
                errors = '; '.join([str(err) for err in result.error_log])
                raise BadMessageStatus(
                    'Request was not schema valid: "{}" for content type "{}"'
                    .format(errors, content_type))
        except etree.XMLSyntaxError as e:
            log.error("Invalid XML received", exc_info=True)
            raise BadMessageStatus('Request was invalid XML', e=e)

    taxii_message = validator_parser.parser(body)

    return taxii_message


def configure_libtaxii_xml_parser(huge_tree=False):
    '''
    Set custom XML parser as a default libtaxii parser
    '''
    # set XML parser in libraxii right away
    set_xml_parser(etree.XMLParser(
        # inject default attributes from DTD or XMLSchema
        attribute_defaults=False,
        # validate against a DTD referenced by the document
        dtd_validation=False,
        # use DTD for parsing
        load_dtd=False,
        # prevent network access for related files (default: True)
        no_network=True,
        # clean up redundant namespace declarations
        ns_clean=True,
        # try hard to parse through broken XML
        recover=False,
        # discard blank text nodes that appear ignorable
        remove_blank_text=False,
        # discard comments
        remove_comments=False,
        #  discard processing instructions
        remove_pis=False,
        # replace CDATA sections by normal text content (default: True)
        strip_cdata=True,
        # save memory for short text content (default: True)
        compact=True,
        # use a hash table of XML IDs for fast access
        # (default: True, always True with DTD validation)
        collect_ids=True,
        # replace entities by their text value (default: True)
        resolve_entities=False,
        # enable/disable security restrictions and support very deep
        # trees and very long text content
        huge_tree=huge_tree))
