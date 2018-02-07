
from opentaxii.signals import (
    CONTENT_BLOCK_CREATED, INBOX_MESSAGE_CREATED, SUBSCRIPTION_CREATED
)


def post_create_content_block(manager, content_block, collection_ids,
                              service_id):
    pass


def post_create_inbox_message(manager, inbox_message):
    pass


def post_create_subscription(manager, subscription):
    pass


CONTENT_BLOCK_CREATED.connect(post_create_content_block)
INBOX_MESSAGE_CREATED.connect(post_create_inbox_message)
SUBSCRIPTION_CREATED.connect(post_create_subscription)
