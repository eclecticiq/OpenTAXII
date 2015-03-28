
class Account(object):
    '''Represents Account entity.

    This class holds user-specific information and is used
    for authorization.

    :param str id: account id
    '''

    def __init__(self, id):
        self.id = id
    
