from datetime import datetime

import pytz
import structlog
from lxml import etree
from libtaxii.common import set_xml_parser

from .exceptions import BadMessageStatus
from .bindings import MESSAGE_VALIDATOR_PARSER

log = structlog.getLogger(__name__)


def get_utc_now():
    return datetime.utcnow().replace(tzinfo=pytz.UTC)


def is_content_supported(supported_bindings, content_binding, version=None):

    if not hasattr(content_binding, 'binding_id') or version == 10:
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
