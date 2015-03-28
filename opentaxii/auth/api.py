
class OpenTAXIIAuthAPI(object):
    '''Abstract class that represents OpenTAXII Authentication API.

    This class defines required methods that need to exist in
    a specific Authentication API implementation.
    '''

    def authenticate(self, username, password):
        '''Authenticate user.

        :param str username: username
        :param str password: user's password

        :return: auth token
        :rtype: string
        '''
        raise NotImplementedError()

    def get_account(self, token):
        '''Get an account by token.

        :param str token: auth token

        :return: an account entity
        :rtype: `opentaxii.entities.Account`
        '''
        raise NotImplementedError()

    def create_account(self, username, password):
        '''Create an account.

        :param str username: username
        :param str password: user's password

        :return: an account entity
        :rtype: `opentaxii.entities.Account`
        '''
        raise NotImplementedError()
