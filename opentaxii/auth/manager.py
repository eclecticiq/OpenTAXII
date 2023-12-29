import structlog
from opentaxii.persistence.exceptions import DoesNotExistError

log = structlog.getLogger(__name__)


class AuthManager:
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
        permission_collections = {}
        # Check for taxii1 collections
        for colname, permission in list(account.permissions.get("taxii1", {}).items()):
            collection = self.server.servers.taxii1.persistence.get_collection(colname)
            if not collection:
                log.warning(
                    "update_account.unknown_collection",
                    collection=colname)
            else:
                permission_collections[colname] = permission

        # Check for taxii2 collections
        for api_root, collections in list(account.permissions.get("taxii2", {}).items()):
            for colname, permission in collections.items():
                try:
                    collection = self.server.servers.taxii2.persistence.get_collection(api_root, colname)
                except DoesNotExistError:
                    log.warning(
                        "update_account.unknown_collection",
                        api_root=api_root, collection=colname)
                else:
                    permission_collections[str(collection.id)] = permission

        account.permissions = permission_collections
        account = self.api.update_account(account, password)
        return account

    def get_accounts(self):
        return self.api.get_accounts()

    def delete_account(self, username):
        return self.api.delete_account(username)
