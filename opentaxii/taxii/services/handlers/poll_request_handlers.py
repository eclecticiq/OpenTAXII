import structlog

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import (
    SD_ITEM, ST_NOT_FOUND, ST_DENIED,
    SD_SUPPORTED_CONTENT, ST_UNSUPPORTED_CONTENT_BINDING,
    RT_FULL,
    ST_PENDING, SD_ESTIMATED_WAIT, SD_RESULT_ID, SD_WILL_PUSH
)

from .base_handlers import BaseMessageHandler
from ...exceptions import StatusMessageException, raise_failure, FailureStatus
from ....persistence.exceptions import ResultsNotReady
from ...converters import (
    content_block_entity_to_content_block, parse_content_bindings,
    content_binding_entities_to_content_bindings
)
from ...utils import get_utc_now

log = structlog.getLogger(__name__)


def retrieve_subscription(service, subscription_id, in_response_to):

    subscription = service.get_subscription(subscription_id)

    if not subscription:
        message = "The subscription requested was not found"
        details = {SD_ITEM: subscription_id}
        raise StatusMessageException(
            ST_NOT_FOUND,
            message=message,
            in_response_to=in_response_to,
            status_details=details)

    return subscription


def retrieve_collection(service, collection_name, in_response_to):

    collection = service.get_collection(collection_name)

    if not collection:
        raise StatusMessageException(
            ST_NOT_FOUND,
            message="The collection requested was not found",
            in_response_to=in_response_to,
            status_details={SD_ITEM: collection_name})

    if not collection.available:
        raise FailureStatus(
            message="The collection is not available",
            in_response_to=in_response_to,
            status_details={SD_ITEM: collection_name})

    return collection


class PollRequest11Handler(BaseMessageHandler):

    supported_request_messages = [tm11.PollRequest]

    @classmethod
    def handle_message(cls, service, request):

        if service.subscription_required and not request.subscription_id:
            raise StatusMessageException(
                ST_DENIED,
                message="Subscription required",
                in_response_to=request.message_id)

        if request.subscription_id and request.poll_parameters:
            message = "Both subscription ID and Poll Parameters present"
            log.warning(message, service_id=service.id,
                        subscription_id=request.subscription_id)

        collection = retrieve_collection(
            service, request.collection_name, request.message_id)

        if request.subscription_id:
            subscription = retrieve_subscription(
                service, request.subscription_id, request.message_id)

            if collection.id != subscription.collection_id:
                raise StatusMessageException(
                    ST_NOT_FOUND,
                    status_details={SD_ITEM: request.collection_name},
                    in_response_to=request.message_id)

            content_bindings = subscription.params.content_bindings
            response_type = subscription.params.response_type
            allow_async = False

        else:
            params = request.poll_parameters
            raw_bindings = params.content_bindings

            requested_bindings = parse_content_bindings(
                raw_bindings, version=11)

            content_bindings = collection.get_matching_bindings(
                requested_bindings)

            if requested_bindings and not content_bindings:

                supported = content_binding_entities_to_content_bindings(
                    collection.supported_content, version=11)

                raise StatusMessageException(
                    ST_UNSUPPORTED_CONTENT_BINDING,
                    in_response_to=request.message_id,
                    status_details={SD_SUPPORTED_CONTENT: supported})

            response_type = params.response_type
            allow_async = params.allow_asynch

        start = request.exclusive_begin_timestamp_label
        end = request.inclusive_end_timestamp_label

        if (start and end) and (start > end):
            message = ("Exclusive begin timestamp label is later "
                       "than inclusive end timestamp label")
            raise_failure(message, request.message_id)

        return cls.prepare_poll_response(
            service=service,
            collection=collection,
            timeframe=(start, end),
            content_bindings=content_bindings,
            in_response_to=request.message_id,
            allow_async=allow_async,
            return_content=(response_type == RT_FULL),
            subscription_id=request.subscription_id
        )

    @classmethod
    def prepare_poll_response(cls, service, collection, in_response_to,
                              timeframe=None, content_bindings=None,
                              result_part=1, allow_async=False,
                              return_content=True, result_id=None,
                              subscription_id=None):

        timeframe = timeframe or (None, None)

        if not any(timeframe) and not content_bindings:
            total_count = collection.volume or 0
        else:
            try:
                total_count = service.get_content_blocks_count(
                    collection, timeframe=timeframe,
                    content_bindings=content_bindings)
            except ResultsNotReady:
                if not allow_async:
                    message = ("The content is not available now and "
                               "the request has allow_asynch set to false")

                    raise_failure(message=message,
                                  in_response_to=in_response_to)

                result_set = service.create_result_set(
                    collection, timeframe=timeframe,
                    content_bindings=content_bindings)

                if not result_set:
                    raise StatusMessageException(
                        ST_DENIED,
                        message="Poll fulfilment is not supported",
                        in_response_to=in_response_to)

                return tm11.StatusMessage(
                    message_id=service.generate_id(),
                    in_response_to=in_response_to,
                    status_type=ST_PENDING,
                    status_detail={
                        SD_ESTIMATED_WAIT: service.wait_time,
                        SD_RESULT_ID: result_set.id,
                        SD_WILL_PUSH: service.can_push
                    }
                )

        # TODO: temporary fix, pending:
        # https://github.com/TAXIIProject/libtaxii/issues/191
        result_part = int(result_part)

        # dividing instead of multiplying to be safe from overflow
        has_more = (float(total_count) / service.max_result_size) > result_part

        capped_count = min(service.max_result_count, total_count)
        is_partial = (capped_count < total_count)

        if has_more and not result_id:
            result_set = service.create_result_set(
                collection,
                timeframe=timeframe,
                content_bindings=content_bindings)
            result_id = result_set.id

        response = tm11.PollResponse(
            message_id=service.generate_id(),
            in_response_to=in_response_to,
            collection_name=collection.name,
            more=has_more,
            result_id=result_id,
            result_part_number=result_part,
            exclusive_begin_timestamp_label=timeframe[0],
            inclusive_end_timestamp_label=timeframe[1],
            # TODO: Temporararily make capped_count an int, pending:
            # https://github.com/TAXIIProject/libtaxii/issues/191
            record_count=tm11.RecordCount(int(capped_count), is_partial),
            subscription_id=subscription_id
        )

        if return_content:

            content_blocks = service.get_content_blocks(
                collection,
                timeframe=timeframe,
                content_bindings=content_bindings,
                part_number=result_part)

            for block in content_blocks:
                response.content_blocks.append(
                    content_block_entity_to_content_block(block, version=11))

        return response


class PollRequest10Handler(BaseMessageHandler):

    supported_request_messages = [tm10.PollRequest]

    @classmethod
    def handle_message(cls, service, request):

        collection = retrieve_collection(service, request.feed_name,
                                         request.message_id)

        if request.subscription_id:
            subscription = retrieve_subscription(
                service, request.subscription_id,
                request.message_id)

            if collection.id != subscription.collection_id:
                details = {SD_ITEM: request.collection_name}
                raise StatusMessageException(
                    ST_NOT_FOUND, status_details=details,
                    in_response_to=request.message_id)

            content_bindings = subscription.params.content_bindings
        else:
            requested_bindings = parse_content_bindings(
                request.content_bindings, version=10)

            content_bindings = collection.get_matching_bindings(
                requested_bindings)

            if requested_bindings and not content_bindings:
                supported_bindings = \
                    content_binding_entities_to_content_bindings(
                        collection.supported_content, version=10)

                details = {SD_SUPPORTED_CONTENT: supported_bindings}
                raise StatusMessageException(
                    ST_UNSUPPORTED_CONTENT_BINDING,
                    in_response_to=request.message_id,
                    status_details=details)

        # Only Data Feeds existed in TAXII 1.0
        if collection.type != collection.TYPE_FEED:
            message = ("The Named Data Collection is not a Data Feed, "
                       "it is a Data Set. Only Data Feeds can be polled "
                       "in TAXII 1.0")
            raise StatusMessageException(
                ST_NOT_FOUND,
                message=message,
                status_details={SD_ITEM: request.feed_name},
                in_response_to=request.message_id)

        start, end = (request.exclusive_begin_timestamp_label,
                      request.inclusive_end_timestamp_label)

        end_response = end or get_utc_now()

        response = tm10.PollResponse(
            message_id=service.generate_id(),
            in_response_to=request.message_id,
            feed_name=collection.name,

            #  FIXME: exclusive/inclusive clash
            inclusive_begin_timestamp_label=start,
            inclusive_end_timestamp_label=end_response,
        )

        content_blocks = service.get_content_blocks(
            collection,
            timeframe=(start, end),
            content_bindings=content_bindings)

        for block in content_blocks:
            response.content_blocks.append(
                content_block_entity_to_content_block(block, version=10))

        return response


class PollRequestHandler(BaseMessageHandler):

    supported_request_messages = [tm10.PollRequest, tm11.PollRequest]

    @classmethod
    def handle_message(cls, service, request):
        if isinstance(request, tm10.PollRequest):
            return PollRequest10Handler.handle_message(service, request)
        elif isinstance(request, tm11.PollRequest):
            return PollRequest11Handler.handle_message(service, request)
        else:
            raise_failure("TAXII Message not supported by message handler",
                          request.message_id)
