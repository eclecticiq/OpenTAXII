from persistence.managers import *
from taxii.entities import *
from taxii.bindings import *


DataCollectionManager.save_data_collection(DataCollectionEntity(
    id = None,
    name = "incoming",
    description = "Some collection A",
    type = "some text type A",
    enabled = True,
    accept_all_content = True,
    supported_content = None,
    content_blocks = []
))

DataCollectionManager.save_data_collection(DataCollectionEntity(
    id = None,
    name = "dummy",
    description = "Some collection B",
    type = "some text type B",
    enabled = True,
    accept_all_content = False,
    supported_content = CONTENT_BINDINGS,
    content_blocks = []
))

