
import signal

from opentaxii.signals import (
    CONTENT_BLOCK_CREATED, INBOX_MESSAGE_CREATED, SUBSCRIPTION_CREATED
)


def post_create_content_block(manager, content_block, collection_ids,
        service_id):
    print 'Content block id=%s (collections=%s, service_id=%s) was created' % (
            content_block.id, ', '.join(map(str, collection_ids)), service_id)


def post_create_inbox_message(manager, inbox_message):
    print 'Inbox message id=%s was created' % inbox_message.id


def post_create_subscription(manager, subscription, service_id):
    print 'Subscription id=%s (service_id=%s) was created' % (subscription.id,
            service_id)


CONTENT_BLOCK_CREATED.connect(post_create_content_block)
INBOX_MESSAGE_CREATED.connect(post_create_inbox_message)
SUBSCRIPTION_CREATED.connect(post_create_subscription)
