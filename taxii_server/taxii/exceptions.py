
import sys

from libtaxii.constants import ST_BAD_MESSAGE, ST_FAILURE, ST_UNSUPPORTED_QUERY


class StatusMessageException(Exception):

    def __init__(self, status_type, in_response_to='0', message=None, status_detail=None,
            extended_headers=None, e=None, **kwargs):

        super(StatusMessageException, self).__init__(e or message, **kwargs)

        self.in_response_to = in_response_to
        self.status_type = status_type
        self.message = message
        self.status_detail = status_detail
        self.extended_headers = extended_headers



class StatusBadMessage(StatusMessageException):

    def __init__(self, message, status_detail=None, extended_headers=None, e=None, **kwargs):
        super(StatusBadMessage, self).__init__(ST_BAD_MESSAGE, message=message,
                status_detail=status_detail, extended_headers=extended_headers, e=e, **kwargs)


class StatusFailureMessage(StatusMessageException):

    def __init__(self, message, status_detail=None, extended_headers=None, e=None, **kwargs):
        super(StatusFailureMessage, self).__init__(ST_FAILURE, message=message,
                status_detail=status_detail, extended_headers=extended_headers, e=e, **kwargs)


class StatusUnsupportedQuery(StatusMessageException):

    def __init__(self, message, status_detail=None, extended_headers=None, e=None, **kwargs):
        super(StatusUnsupportedQuery, self).__init__(ST_UNSUPPORTED_QUERY, message=message,
                status_detail=status_detail, extended_headers=extended_headers, e=e, **kwargs)


def raise_failure(message, in_response_to='0'):
    et, ei, tb = sys.exc_info()
    raise StatusFailureMessage(message, in_response_to=in_response_to, e=ei), None, tb

