
from .queue import push
from .utils import date_to_ts

from settings import INBOX_QUEUE

def post_content_block_save(content_block_entity, inbox_message_entity, collections):

    blob = dict(
        content_id = content_block_entity.id,

        source = None,
        source_collection = None,

        sink_collections = [c.name for c in collections],

        content = content_block_entity.content,
        binding = content_block_entity.content_binding,

        timestamp = date_to_ts(content_block_entity.timestamp_label),
    )
    push(INBOX_QUEUE, blob)



