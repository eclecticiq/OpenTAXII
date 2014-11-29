
import sys
import libtaxii as t
import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import *
from libtaxii.common import generate_message_id


class StatusMessageException(Exception):
    """
    StatusMessageException is an exception that can be raised and can be caught by
    TaxiiStatusMessageMiddleware. This class holds all the information necessary to
    create either a TAXII 1.1 or TAXII 1.0 Status Message.
    """
    def __init__(self, status_type, in_response_to=None, message=None, status_detail=None, extended_headers=None, e=None, **kwargs):
        """
        Arguments:
            in_response_to (string) - The message_id of the request
            status_type (string) - The Status Type for the Status Message
            message (string) - A string message for the Status Message
            status_details (dict) - A dictionary containing the status details for the Status Message
            extended_headers (dict) - The extended headers for the Status Message
        """
        super(StatusMessageException, self).__init__(e or message, **kwargs)

        self.in_response_to = in_response_to
        self.status_type = status_type
        self.message = message
        self.status_detail = status_detail
        self.extended_headers = extended_headers



class StatusBadMessage(StatusMessageException):

    def __init__(self, message, status_detail=None, extended_headers=None, e=None, **kwargs):
        super(StatusBadMessage, self).__init__(ST_BAD_MESSAGE, message=message, status_detail=status_detail, extended_headers=extended_headers, e=e, **kwargs)

class StatusFailureMessage(StatusMessageException):

    def __init__(self, message, status_detail=None, extended_headers=None, e=None, **kwargs):
        super(StatusFailureMessage, self).__init__(ST_FAILURE, message=message, status_detail=status_detail, extended_headers=extended_headers, e=e, **kwargs)


class StatusUnsupportedQuery(StatusMessageException):

    def __init__(self, message, status_detail=None, extended_headers=None, e=None, **kwargs):
        super(StatusUnsupportedQuery, self).__init__(ST_UNSUPPORTED_QUERY, message=message, status_detail=status_detail,
                extended_headers=extended_headers, e=e, **kwargs)


def raise_failure(message, in_response_to=None):
    et, ei, tb = sys.exc_info()
    raise StatusFailureMessage(message, in_response_to=in_response_to, e=ei), None, tb

