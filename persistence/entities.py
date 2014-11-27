from collections import namedtuple

DataCollectionEntity = namedtuple("DataCollectionEntity", ["id", "name", "description", "type", "enabled", "accept_all_content"])

class DataCollectionEntity(Entity):
    pass

#    def __init__(self, 
