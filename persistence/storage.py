
class AbstractStorage(object):

    def __init__(self):
        pass

    def get_collections(self):
        raise NotImplementedError()

    def store_inbox_message(self, inbox_message):
        raise NotImplementedError()

    def create_collection(self, entity):
        raise NotImplementedError()


    
