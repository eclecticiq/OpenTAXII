
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

    def update_account(self, account, password):
        '''Create an account.

        :param str username: username
        :param str password: password

        :return: an account entity
        :rtype: `opentaxii.entities.Account`
        '''
        raise NotImplementedError()

    def get_accounts(self):
        raise NotImplementedError()

    def delete_account(self, username):
        raise NotImplementedError()
