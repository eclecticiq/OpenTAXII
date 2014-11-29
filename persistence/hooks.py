
from .queue import push

from settings import INBOX_QUEUE

def post_content_block_save(content_block_entity, inbox_message_entity, collections):

    push(INBOX_QUEUE, dict(
        content_id = content_block_entity.id,
        collections = [c.name for c in collections],
        content = content_block_entity.content
    ))



