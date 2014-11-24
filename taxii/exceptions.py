
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
    def __init__(self, status_type, in_response_to=None, message=None, status_detail=None, extended_headers=None, **kwargs):
        """
        Arguments:
            in_response_to (string) - The message_id of the request
            status_type (string) - The Status Type for the Status Message
            message (string) - A string message for the Status Message
            status_details (dict) - A dictionary containing the status details for the Status Message
            extended_headers (dict) - The extended headers for the Status Message
        """
        super(StatusMessageException, self).__init__(message, **kwargs)

        self.in_response_to = in_response_to
        self.status_type = status_type
        self.message = message
        self.status_detail = status_detail
        self.extended_headers = extended_headers



class StatusBadMessage(StatusMessageException):

    def __init__(self, message, status_detail=None, extended_headers=None, **kwargs):
        super(StatusBadMessage, self).__init__(ST_BAD_MESSAGE, message, status_detail=status_detail, extended_headers=extended_headers, **kwargs)



class StatusUnsupportedQuery(StatusMessageException):

    def __init__(self, message, status_detail=None, extended_headers=None, **kwargs):
        super(StatusUnsupportedQuery, self).__init__(ST_UNSUPPORTED_QUERY, message=message, status_detail=status_detail, extended_headers=extended_headers, **kwargs)


def raise_failure(message, in_response_to=None):
    raise StatusMessageException(ST_FAILURE, in_response_to=in_response_to, message=message)

