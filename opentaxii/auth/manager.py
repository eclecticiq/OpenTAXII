import structlog

log = structlog.getLogger(__name__)


class AuthManager(object):
    '''Manager responsible for authentication.

    Manager uses API instance ``api`` for basic auth operations and
    provides additional logic on top.

    :param `opentaxii.auth.api.OpenTAXIIAuthAPI` api:
        instance of Auth API class
    '''

    def __init__(self, api):
        self.api = api

    def authenticate(self, username, password):
        '''Authenticate a user.

        :param str username: username
        :param str password: password

        :return: auth token
        :rtype: string
        '''
        return self.api.authenticate(username, password)

    def get_account(self, token):
        '''Get account for auth token.

        :param str token: auth token

        :return: an account entity
        :rtype: `opentaxii.entities.Account`
        '''
        return self.api.get_account(token)

    def create_account(self, username, password):
        '''Create an account.

        NOTE: Additional method that is only used in the helper scripts
        shipped with OpenTAXII.
        '''
        account = self.api.create_account(username, password)
        log.info("account.created", username=account.username)

        return account
