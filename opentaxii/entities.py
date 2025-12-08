import uuid
from typing import Literal


class Account:
    '''Represents Account entity.

    This class holds user-specific information and is used for authorization.

    :param id: account id
    :param permissions: A dictionary where the key is the collection identifier
        and the value either "read" or "modify". The identifier for TAXII1
        collection is a string name while it is a UUID for TAXII2
    :param details: additional details of an account
    '''

    def __init__(
        self,
        id,
        username: str,
        permissions: dict[str | uuid.UUID, Literal["read", "modify"]],
        is_admin: bool = False,
        **details,
    ):
        self.id = id
        self.username = username
        self.permissions = permissions
        self.is_admin = is_admin
        self.details = details

    def __repr__(self):
        return 'Account(username={}, is_admin={})'.format(self.username, self.is_admin)
