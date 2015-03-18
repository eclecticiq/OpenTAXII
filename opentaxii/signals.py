from blinker import signal

CONTENT_BLOCK_CREATED = signal('opentaxii.content_block.created')
INBOX_MESSAGE_CREATED = signal('opentaxii.inbox_message.created')
SUBSCRIPTION_CREATED = signal('opentaxii.subscription.created')
