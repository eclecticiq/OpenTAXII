import sys
import six
from libtaxii.constants import (
    ST_BAD_MESSAGE, ST_FAILURE, ST_UNAUTHORIZED
)


class StatusMessageException(Exception):

    def __init__(self, status_type, in_response_to='0', message=None,
                 status_details=None, extended_headers=None, e=None):

        super(StatusMessageException, self).__init__(
            e or message or status_type)

        self.in_response_to = in_response_to
        self.status_type = status_type
        self.message = message
        self.status_details = status_details
        self.extended_headers = extended_headers


class BadMessageStatus(StatusMessageException):

    def __init__(self, message, **kwargs):
        super(BadMessageStatus, self).__init__(
            ST_BAD_MESSAGE, message=message, **kwargs)


class FailureStatus(StatusMessageException):

    def __init__(self, message, **kwargs):
        super(FailureStatus, self).__init__(
            ST_FAILURE, message=message, **kwargs)


class UnauthorizedStatus(StatusMessageException):

    def __init__(self, **kwargs):
        super(UnauthorizedStatus, self).__init__(ST_UNAUTHORIZED, **kwargs)


def raise_failure(message, in_response_to='0'):
    _, ei, tb = sys.exc_info()
    six.reraise(
        FailureStatus,
        FailureStatus(message, in_response_to=in_response_to, e=ei),
        tb=tb)
