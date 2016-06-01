
class Account(object):
    '''Represents Account entity.

    This class holds user-specific information and is used
    for authorization.

    :param str id: account id
    :param dict details: additional details of an account
    '''

    def __init__(self, id, username, **details):

        self.id = id
        self.username = username
        self.details = details
