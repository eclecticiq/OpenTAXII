
class OpenTAXIIAuthAPI(object):
    '''Abstract class that represents OpenTAXII Authentication API.

    This class defines required methods that need to exist in
    a specific Authentication API implementation.
    '''

    def init_app(self, app):
        pass

    def authenticate(self, username, password):
        '''Authenticate a user.

        :param str username: username
        :param str password: password

        :return: auth token
        :rtype: string
        '''
        raise NotImplementedError()

    def get_account(self, token):
        '''Get account for auth token.

        :param str token: auth token

        :return: an account entity
        :rtype: `opentaxii.entities.Account`
        '''
        raise NotImplementedError()

    def create_account(self, username, password):
        '''Create an account.

        NOTE: Additional method that is only used in the helper scripts
        shipped with OpenTAXII.
        '''
        raise NotImplementedError()
