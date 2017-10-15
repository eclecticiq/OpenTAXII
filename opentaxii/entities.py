
class Account(object):
    '''Represents Account entity.

    This class holds user-specific information and is used
    for authorization.

    :param str id: account id
    :param dict details: additional details of an account
    '''

    def __init__(
            self, id, username, permissions, is_admin=False, **details):
        self.id = id
        self.username = username
        self.permissions = permissions
        self.is_admin = is_admin
        self.details = details

    def can_read(self, collection_name):
        return (
            self.is_admin or
            self.permissions.get(collection_name) in ('read', 'modify'))

    def can_modify(self, collection_name):
        return (
            self.is_admin or
            self.permissions.get(collection_name) == 'modify')

    def __repr__(self):
        return (
            'Account(username={}, is_admin={})'
            .format(self.username, self.is_admin))
