from typing import Literal


class Account:
    '''Represents Account entity.

    This class holds user-specific information and is used for authorization.

    The permissions are defined as follow:

    1. key: A collection identifier. For TAXII1 collection, it is a string name
       while it is a stringified UUID for TAXII2.

    2. value: The permission level. For TAXII1 collection, it is a string with
       either "read" or "modify" value. However for TAXII2, it is a list with
       one or both values: "read" and "write". The reason is that TAXII2 allows
       to write without read access and vice versa.
    '''

    def __init__(
        self,
        id,
        username: str,
        permissions: dict[
            str, Literal["read", "modify"] | list[Literal["read", "write"]]
        ],
        is_admin: bool = False,
        **details,
    ):
        """
        :param id: account id
        :param permissions: A dictionary where the key is the collection identifier
            and the value the permission level.
        :param details: additional details of an account
        """
        self.id = id
        self.username = username
        self.permissions = permissions
        self.is_admin = is_admin
        self.details = details

    def __repr__(self):
        return 'Account(username={}, is_admin={})'.format(self.username, self.is_admin)
