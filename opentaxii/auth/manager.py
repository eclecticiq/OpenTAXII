
class AuthManager(object):

    def __init__(self, api):
        self.api = api

    def authenticate(self, username, password):
        return self.api.authenticate(username, password)

    def get_account(self, token):
        return self.api.get_account(token)

    def create_account(self, username, password):
        return self.api.create_account(username, password)
