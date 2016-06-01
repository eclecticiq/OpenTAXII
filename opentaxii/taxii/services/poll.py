import structlog

from libtaxii.constants import (
    MSG_POLL_REQUEST, MSG_POLL_FULFILLMENT_REQUEST, SVC_POLL
)

from ..entities import ResultSetEntity
from .abstract import TAXIIService
from .handlers import PollRequestHandler, PollFulfilmentRequestHandler

log = structlog.getLogger(__name__)

DEFAULT_MAX_RESULT_SIZE = 1000000
DEFAULT_MAX_RESULT_COUNT = 10 * DEFAULT_MAX_RESULT_SIZE


class PollService(TAXIIService):

    handlers = {
        MSG_POLL_REQUEST: PollRequestHandler,
        MSG_POLL_FULFILLMENT_REQUEST: PollFulfilmentRequestHandler
    }

    service_type = SVC_POLL

    subscription_required = False

    # Random sane number
    wait_time = 300

    # Poll Service does not support pushing for now
    can_push = False

    max_result_size = None
    max_result_count = None

    def __init__(self, subscription_required=False, max_result_size=-1,
                 max_result_count=-1, **kwargs):

        super(PollService, self).__init__(**kwargs)

        self.subscription_required = subscription_required

        self.max_result_size = (
            max_result_size if max_result_size >= 0
            else DEFAULT_MAX_RESULT_SIZE)

        self.max_result_count = (
            max_result_count if max_result_count >= 0
            else DEFAULT_MAX_RESULT_COUNT)

    def get_collection(self, name):
        return self.server.persistence.get_collection(name, self.id)

    def get_offset_limit(self, part_number):

        offset = (part_number - 1) * self.max_result_size
        limit = self.max_result_size

        return offset, limit

    def get_content_blocks_count(self, collection, timeframe=None,
                                 content_bindings=None):

        start_time, end_time = timeframe or (None, None)

        return self.server.persistence.get_content_blocks_count(
            collection_id=collection.id,
            start_time=start_time,
            end_time=end_time,
            bindings=content_bindings
        )

    def get_content_blocks(self, collection, timeframe=None,
                           content_bindings=None, part_number=1):

        start_time, end_time = timeframe or (None, None)
        offset, limit = self.get_offset_limit(part_number)

        return self.server.persistence.get_content_blocks(
            collection_id=collection.id,
            start_time=start_time,
            end_time=end_time,
            bindings=content_bindings,
            offset=offset,
            limit=limit,
        )

    def create_result_set(self, collection, content_bindings=None,
                          timeframe=None):

        entity = ResultSetEntity(
            id=self.generate_id(),
            collection_id=collection.id,
            content_bindings=content_bindings,
            timeframe=timeframe
        )

        return self.server.persistence.create_result_set(entity)

    def get_result_set(self, result_set_id):
        return self.server.persistence.get_result_set(result_set_id)

    def get_subscription(self, subscription_id):
        return self.server.persistence.get_subscription(subscription_id)
