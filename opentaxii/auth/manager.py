import structlog

log = structlog.getLogger(__name__)


class AuthManager(object):
    '''Manager responsible for authentication.

    Manager uses API instance ``api`` for basic auth operations and
    provides additional logic on top.

    :param `opentaxii.auth.api.OpenTAXIIAuthAPI` api:
        instance of Auth API class
    '''

    def __init__(self, server, api):
        self.server = server
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

    def update_account(self, account, password):
        '''Create an account.

        NOTE: Additional method that is only used in the helper scripts
        shipped with OpenTAXII.
        '''
        for colname, permission in list(account.permissions.items()):
            collection = self.server.persistence.get_collection(colname)
            if not collection:
                log.warning(
                    "update_account.unknown_collection",
                    collection=colname)
                account.permissions.pop(colname)
        account = self.api.update_account(account, password)
        return account

    def get_accounts(self):
        return self.api.get_accounts()

    def delete_account(self, username):
        return self.api.delete_account(username)
