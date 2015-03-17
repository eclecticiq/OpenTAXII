
class OpenTAXIIAuthAPI(object):

    def authenticate(self, username, password):
        raise NotImplementedError()

    def get_account(self, token):
        raise NotImplementedError()

    def create_account(self, username, password):
        raise NotImplementedError()
