
from .taxii.exceptions import UnauthorizedStatus


class UnauthorizedException(UnauthorizedStatus):
    pass


class InvalidAuthHeader(Exception):
    pass
