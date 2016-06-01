import pytest

from libtaxii import messages_10 as tm10
from libtaxii import messages_11 as tm11
from libtaxii.constants import VID_TAXII_XML_10, VID_TAXII_XML_11

from opentaxii.taxii import exceptions
from opentaxii.taxii.utils import parse_message

MESSAGE_ID = '123'


@pytest.mark.parametrize("content_type", [VID_TAXII_XML_10, VID_TAXII_XML_11])
def test_parse_message(content_type):

    with pytest.raises(exceptions.BadMessageStatus):
        parse_message(content_type, 'invalid-body', do_validate=True)

    tm = (tm10 if content_type == VID_TAXII_XML_10 else tm11)

    parsed = parse_message(
        content_type,
        tm.DiscoveryRequest(MESSAGE_ID).to_xml(),
        do_validate=True)

    assert isinstance(parsed, tm.DiscoveryRequest)
    assert parsed.message_id == MESSAGE_ID
