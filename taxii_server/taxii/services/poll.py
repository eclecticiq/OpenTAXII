import sys

from libtaxii.constants import (
        MSG_POLL_REQUEST, SVC_POLL
)

from .abstract import TaxiiService
from .handlers import PollRequestHandler
from ..exceptions import StatusMessageException

import structlog
log = structlog.getLogger(__name__)


class PollService(TaxiiService):

    handlers = {
        MSG_POLL_REQUEST : PollRequestHandler,
        #MSG_POLL_FULFILLMENT_REQUEST 
    }
            
    service_type = SVC_POLL

    subscription_required = False

    def __init__(self, subscription_required=False, max_result_size=-1,
            max_result_count=-1, **kwargs):
        super(PollService, self).__init__(**kwargs)

        self.subscription_required = subscription_required

        self.max_result_size = max_result_size if max_result_size >= 0 else sys.maxint
        self.max_result_count = max_result_count if max_result_count >= 0 else sys.maxint


    def get_collection(self, name):
        return self.server.data_manager.get_collection(name, self.id)


    def get_offset_limit(self, part_number):

        offset = (part_number - 1) * self.max_result_size
        limit = self.max_result_size

        return offset, limit


    def get_content_count(self, collection, timeframe=None,
            content_bindings=[], part_number=1):

        start_time, end_time = timeframe or (None, None)

        return self.server.data_manager.get_content_count(
            collection_id = collection.id,
            start_time = start_time,
            end_time = end_time,
            bindings = content_bindings
        )


    def get_content(self, collection, timeframe=None,
            content_bindings=[], part_number=1):

        start_time, end_time = timeframe or (None, None)

        offset, limit = self.get_offset_limit(part_number)

        return self.server.data_manager.get_content(
            collection_id = collection.id,
            start_time = start_time,
            end_time = end_time,
            bindings = content_bindings,
            offset = offset,
            limit = limit,
        )


    def create_result_set(self):
        pass

        #expires = models.DateTimeField()

