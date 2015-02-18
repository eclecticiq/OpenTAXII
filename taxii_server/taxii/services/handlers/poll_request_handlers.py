
import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import *
from libtaxii.common import generate_message_id

from .base_handlers import BaseMessageHandler
from ...exceptions import StatusMessageException, raise_failure
from ....data.exceptions import ResultsNotReady

from ...entities import CollectionEntity
from ...transform import to_content_bindings
from ...utils import get_utc_now



import structlog
log = structlog.getLogger(__name__)


class PollRequest11Handler(BaseMessageHandler):

    supported_request_messages = [tm11.PollRequest]

    @classmethod
    def create_pending_response(cls, service, prp, content):
        """
        Arguments:
            poll_service (models.PollService) - The TAXII Poll Service being invoked
            prp (util.PollRequestProperties) - The Poll Request Properties of the Poll Request
            content - A list of content (nominally, models.ContentBlock objects).

        This method returns a StatusMessage with a Status Type
        of Pending OR raises a StatusMessageException
        based on the following table::

            asynch | Delivery_Params | can_push || Response Type
            ----------------------------------------------------
            True   | -               | -        || Pending - Asynch
            False  | Yes             | Yes      || Pending - Push
            False  | Yes             | No       || StatusMessageException
            False  | No              | -        || StatusMessageException
        """

        # Identify the Exception conditions first (e.g., rows #3 and #4)
        if (prp.allow_asynch is False and
            (prp.delivery_parameters is None or prp.can_push is False)):

            raise StatusMessageException(prp.message_id,
                                         ST_FAILURE,
                                         "The content was not available now and \
                                         the request had allow_asynch=False and no \
                                         Delivery Parameters were specified.")

        # Rows #1 and #2 are both Status Messages with a type of Pending
        result_set = cls.create_result_set(content, prp, poll_service)
        sm = tm11.StatusMessage(message_id=generate_message_id(),
                                in_response_to=prp.message_id,
                                status_type=ST_PENDING)
        if prp.allow_asynch:
            sm.status_details = {SD_ESTIMATED_WAIT: 300, SD_RESULT_ID: result_set.pk, SD_WILL_PUSH: False}
        else:
            # TODO: Check and see if the requested delivery parameters are supported
            sm.status_details = {SD_ESTIMATED_WAIT: 300, SD_RESULT_ID: result_set.pk, SD_WILL_PUSH: True}
            # TODO: Need to try pushing or something.
        return sm


    @classmethod
    def handle_message(cls, service, request):

        collection = service.get_collection(request.collection_name)

        if not collection:
            message = 'The collection you requested was not found'
            details = {SD_ITEM: name}
            raise StatusMessageException(ST_NOT_FOUND, message=message,
                    in_response_to=request.message_id, status_details=details)

        timeframe = (request.exclusive_begin_timestamp_label,
                request.inclusive_end_timestamp_label)

        params = request.poll_parameters

        requested_bindings = to_content_bindings(params.content_bindings, version=11)
        content_bindings = collection.get_matching_bindings(requested_bindings)

        if requested_bindings and not content_bindings:
            details = {SD_SUPPORTED_CONTENT: collection.get_supported_content(version=11)}
            raise StatusMessageException(ST_UNSUPPORTED_CONTENT_BINDING,
                    in_response_to=request.message_id, status_details=details)

        if (request.inclusive_end_timestamp_label and request.exclusive_begin_timestamp_label) and \
            request.exclusive_begin_timestamp_label > request.inclusive_end_timestamp_label :

                message = "Exclusive begin timestamp label is later than inclusive end timestamp label"
                raise_failure(message, request.message_id)


        result_part = 1

        try:
            total_count = service.get_content_count(collection,
                    timeframe=timeframe, content_bindings=content_bindings)

        except ResultsNotReady:
            raise Exception('Not implemented yet')
            return cls.create_pending_response(poll_service, prp, content_blocks)

        has_more = total_count > (result_part * service.max_result_size)
        capped_count = min(service.max_result_count, total_count)
        is_partial = (capped_count < total_count)

        if has_more:
            # create ResultSet
            result_set = service.create_result_set(
                collection = collection,
                total_count = total_count,
                last_part_returned = result_part
                #subscription
            )
            result_id = result_set.id
        else:
            result_id = None

        response = tm11.PollResponse(
            message_id = generate_message_id(),
            in_response_to = request.message_id,
            collection_name = collection.name,

            more = has_more,
            result_id = result_id,
            result_part_number = result_part,

            exclusive_begin_timestamp_label = request.exclusive_begin_timestamp_label,
            inclusive_end_timestamp_label = request.inclusive_end_timestamp_label,
            record_count = tm11.RecordCount(capped_count, is_partial),
            # subscription_id
        )

        #count_only = (params.response_type == RT_COUNT_ONLY)
        if params.response_type == RT_FULL:

            content_blocks = service.get_content(collection, timeframe=timeframe,
                    content_bindings=content_bindings, part_number=result_part)

            for block in content_blocks:
                response.content_blocks.append(to_content_block(block, version=11))

        return response



class PollRequest10Handler(BaseMessageHandler):

    supported_request_messages = [tm10.PollRequest]

    @classmethod
    def handle_message(cls, service, request):

        collection = service.get_collection(request.feed_name)

        requested_bindings = to_content_bindings(request.content_bindings, version=10)
        content_bindings = collection.get_matching_bindings(requested_bindings)

         # Only Data Feeds existed in TAXII 1.0
        if collection.type != collection.TYPE_FEED:
            message = "The Named Data Collection is not a Data Feed, it is a Data Set. " + \
                      "Only Data Feeds can be polled in TAXII 1.0"
            details = {SD_ITEM: request.feed_name}
            raise StatusMessageException(ST_NOT_FOUND, message=message,
                    status_details=details, in_response_to=request.message_id)

        timeframe = (request.exclusive_begin_timestamp_label,
                request.inclusive_end_timestamp_label)

        if request.inclusive_end_timestamp_label:
            end_ts = request.inclusive_end_timestamp_label
        else:
            end_ts = get_utc_now()

        response = tm10.PollResponse(
            message_id = generate_message_id(),
            in_response_to = request.message_id,
            feed_name = collection.name,

            inclusive_begin_timestamp_label = request.exclusive_begin_timestamp_label,
            inclusive_end_timestamp_label = end_ts,
        )

        content_blocks = service.get_content(collection, timeframe=timeframe,
                content_bindings=content_bindings)

        for block in content_blocks:
            response.content_blocks.append(to_content_block(block, version=10))

        return response


class PollRequestHandler(BaseMessageHandler):

    supported_request_messages = [tm10.PollRequest, tm11.PollRequest]

    @staticmethod
    def handle_message(service, request):
        if isinstance(request, tm10.PollRequest):
            return PollRequest10Handler.handle_message(service, request)
        elif isinstance(request, tm11.PollRequest):
            return PollRequest11Handler.handle_message(service, request)
        else:
            raise_failure("TAXII Message not supported by message handler", request.message_id)






def to_content_block(entity, version):

    if version == 10:

        content_binding = entity.content_binding.binding
        cb = tm10.ContentBlock(
            content_binding = content_binding,
            content = entity.content,
            timestamp_label = entity.timestamp_label,
        )

    elif version == 11:
        content_binding = tm11.ContentBinding(
            entity.content_binding.binding,
            subtype_ids = entity.content_binding.subtypes
        )
        cb = tm11.ContentBlock(
            content_binding = content_binding,
            content = entity.content,
            timestamp_label = entity.timestamp_label,
            message = entity.message,
        )

    return cb




#@staticmethod
#def from_poll_request_10(poll_service, poll_request):
#    prp = PollRequestProperties()
#    prp.poll_request = poll_request
#    prp.message_id = poll_request.message_id
#    prp.collection = poll_service.validate_collection_name(poll_request.feed_name, poll_request.message_id)
#
#    if poll_request.subscription_id:
#        try:
#            s = models.Subscription.objects.get(subscription_id=poll_request.subscription_id)
#            prp.subscription = s
#        except models.Subscription.DoesNotExist:
#            raise StatusMessageException(poll_request.message_id,
#                                         ST_NOT_FOUND,
#                                         status_detail={SD_ITEM: poll_request.subscription_id})
#        prp.response_type = None
#        prp.content_bindings = s.content_binding.all()
#        prp.allow_asynch = None
#        prp.delivery_parameters = s.delivery_parameters
#    else:
#        prp.response_type = None
#        prp.content_bindings = prp.collection.get_binding_intersection_10(poll_request.content_bindings, prp.message_id)
#        prp.delivery_parameters = None
#
#    if prp.collection.type != CT_DATA_FEED:  # Only Data Feeds existed in TAXII 1.0
#        raise StatusMessageException(poll_request.message_id,
#                                     ST_NOT_FOUND,
#                                     "The Named Data Collection is not a Data Feed, it is a Data Set. "
#                                     "Only Data Feeds can be"
#                                     "Polled in TAXII 1.0",
#                                     {SD_ITEM: poll_request.feed_name})
#
#    current_datetime = datetime.datetime.now(tzutc())
#    # If the request specifies a timestamp label in an acceptable range, use it.
#    # Otherwise, don't use a begin timestamp label
#    if poll_request.exclusive_begin_timestamp_label:
#        pr_ebtl = poll_request.exclusive_begin_timestamp_label
#        if pr_ebtl < current_datetime:
#            prp.exclusive_begin_timestamp_label = poll_request.exclusive_begin_timestamp_label
#
#    # Use either the specified end timestamp label;
#    # or the current time iff the specified end timestmap label is after the current time
#    prp.inclusive_end_timestamp_label = current_datetime
#    if poll_request.inclusive_end_timestamp_label:
#        pr_ietl = poll_request.inclusive_end_timestamp_label
#        if pr_ietl < current_datetime:
#            prp.inclusive_end_timestamp_label = poll_request.inclusive_end_timestamp_label
#
#    if ((prp.inclusive_end_timestamp_label is not None and prp.exclusive_begin_timestamp_label is not None) and
#        prp.inclusive_end_timestamp_label < prp.exclusive_begin_timestamp_label):
#        raise StatusMessageException(prp.message_id,
#                                     ST_FAILURE,
#                                     message="Invalid Timestamp Labels: End TS Label is earlier "
#                                             "than Begin TS Label")
#
#    return prp
#
