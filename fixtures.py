from persistence import *
from taxii.bindings import *

DataCollectionEntity(
    id = None,
    name = "collection-a",
    description = "Some collection A",
    type = "some text type A",
    enabled = True,
    accept_all_content = True,
    supported_content = None
).save()

DataCollectionEntity(
    id = None,
    name = "collection-b",
    description = "Some collection B",
    type = "some text type B",
    enabled = True,
    accept_all_content = False,
    supported_content = CONTENT_BINDINGS
).save()

