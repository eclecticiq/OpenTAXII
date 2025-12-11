from opentaxii.entities import Account


class OpenTAXIIAuthAPI:
    '''Abstract class that represents OpenTAXII Authentication API.

    This class defines required methods that need to exist in
    a specific Authentication API implementation.
    '''

    def init_app(self, app):
        pass

    def authenticate(self, username: str, password: str) -> str | None:
        '''Authenticate a user.

        :param username: username
        :param password: password

        :return: auth token
        '''
        raise NotImplementedError()

    def get_account(self, token: str) -> Account | None:
        '''Get account for auth token.

        :param token: auth token
        '''
        raise NotImplementedError()

    def create_account(
        self, username: str, password: str, is_admin: bool = False
    ) -> Account:
        '''Create an account.'''
        raise NotImplementedError()

    def update_account(self, obj: Account, password: str | None = None) -> Account:
        '''Update an account.

        :param AccountEntity obj: an ipdated user entity (old one matched by username)
        :param password: a new password
        '''
        raise NotImplementedError()

    def get_accounts(self):
        raise NotImplementedError()

    def delete_account(self, username: str):
        raise NotImplementedError()
