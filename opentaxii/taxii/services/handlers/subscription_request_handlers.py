import structlog

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import (
    SD_SUPPORTED_CONTENT, ST_UNSUPPORTED_CONTENT_BINDING,
    SD_ITEM, ST_NOT_FOUND, ST_BAD_MESSAGE,
    ACT_SUBSCRIBE, ACT_UNSUBSCRIBE, ACT_PAUSE,
    ACT_RESUME, ACT_STATUS, ACT_TYPES_11,
    ACT_TYPES_10
)

from ...exceptions import StatusMessageException, raise_failure
from ...converters import (
    subscription_to_subscription_instance,
    parse_content_bindings
)
from ...entities import PollRequestParametersEntity, SubscriptionEntity

from .base_handlers import BaseMessageHandler
from .poll_request_handlers import retrieve_collection

log = structlog.getLogger(__name__)


def action_subscribe(request, service, collection, version, **kwargs):

    if version == 11:
        params = request.subscription_parameters
        response_type = params.response_type

        if len(params.content_bindings) == 0:
            supported_contents = []
        else:
            requested_bindings = parse_content_bindings(
                params.content_bindings,
                version=version)

            supported_contents = \
                collection.get_matching_bindings(requested_bindings)

            if requested_bindings and not supported_contents:
                supported = collection.get_supported_content(version=version)
                details = {SD_SUPPORTED_CONTENT: supported}
                raise StatusMessageException(
                    ST_UNSUPPORTED_CONTENT_BINDING,
                    in_response_to=request.message_id,
                    status_details=details)

    else:
        supported_contents = []
        response_type = None

    poll_request_params = PollRequestParametersEntity(
        response_type=response_type,
        content_bindings=supported_contents,
    )

    # we are ignoring Delivery Parameters for now

    subscription = SubscriptionEntity(
        service_id=service.id,
        collection_id=collection.id,
        poll_request_params=poll_request_params,
        status=SubscriptionEntity.ACTIVE
    )

    return service.create_subscription(subscription)


def action_unsubscribe(request, service, subscription, **kwargs):
    if subscription:
        subscription.status = SubscriptionEntity.UNSUBSCRIBED
        return service.update_subscription(subscription)
    else:
        # Spec says that unsubscribe should be successful even
        # if subscription doesn't exist
        return SubscriptionEntity(
            collection_id=None,
            service_id=service.id,
            subscription_id=request.subscription_id,
            status=SubscriptionEntity.UNSUBSCRIBED)


def action_status(service, subscription, **kwargs):
    if subscription:
        return subscription
    else:
        return service.get_subscriptions()


def action_pause(service, subscription, **kwargs):
    if subscription.status == SubscriptionEntity.PAUSED:
        return subscription
    subscription.status = SubscriptionEntity.PAUSED
    return service.update_subscription(subscription)


def action_resume(service, subscription, **kwargs):
    if subscription.status != SubscriptionEntity.PAUSED:
        return subscription
    subscription.status = SubscriptionEntity.ACTIVE
    return service.update_subscription(subscription)


ACTIONS = {
    ACT_SUBSCRIBE: action_subscribe,
    ACT_UNSUBSCRIBE: action_unsubscribe,
    ACT_PAUSE: action_pause,
    ACT_RESUME: action_resume,
    ACT_STATUS: action_status
}


class SubscriptionRequest11Handler(BaseMessageHandler):

    supported_request_messages = [tm11.ManageCollectionSubscriptionRequest]

    @classmethod
    def validate_request(cls, request, subscription):

        action = request.action

        if action not in ACT_TYPES_11:
            error_message = "The specified action was invalid"

        elif action in (ACT_UNSUBSCRIBE, ACT_PAUSE, ACT_RESUME) \
                and not request.subscription_id:
            error_message = 'Action "%s" requires a subscription id' % action

        else:
            error_message = None

        if error_message:
            raise StatusMessageException(
                ST_BAD_MESSAGE,
                message=error_message,
                in_response_to=request.message_id)

        if (not subscription and (
                action in (ACT_PAUSE, ACT_RESUME) or
                (action == ACT_STATUS and request.subscription_id))):

            details = {SD_ITEM: request.subscription_id}
            raise StatusMessageException(
                ST_NOT_FOUND,
                status_details=details,
                in_response_to=request.message_id)

    @classmethod
    def handle_message(cls, service, request):

        if request.subscription_id:
            subscription = service.get_subscription(request.subscription_id)
        else:
            subscription = None

        cls.validate_request(request, subscription)

        collection = retrieve_collection(service,
                                         request.collection_name,
                                         request.message_id)

        if subscription and subscription.collection_id != collection.id:
            raise StatusMessageException(
                ST_NOT_FOUND,
                status_details={SD_ITEM: request.collection_name},
                in_response_to=request.message_id)

        response = tm11.ManageCollectionSubscriptionResponse(
            message_id=cls.generate_id(),
            in_response_to=request.message_id,
            collection_name=collection.name,
            message=service.subscription_message,
        )

        result = ACTIONS[request.action](
            service=service, request=request, collection=collection,
            subscription=subscription, version=11)

        if isinstance(result, (list, tuple)):
            results = result
        else:
            results = [result]

        polling_services = service.get_polling_services(collection)

        for _result in results:
            instance = subscription_to_subscription_instance(
                subscription=_result,
                polling_services=polling_services,
                version=11,
                subscription_parameters=_result.params
            )

            response.subscription_instances.append(instance)

        return response


class SubscriptionRequest10Handler(BaseMessageHandler):
    supported_request_messages = [tm10.ManageFeedSubscriptionRequest]

    @classmethod
    def validate_request(cls, request):

        action = request.action

        if action not in ACT_TYPES_10:
            error_message = "The specified action was invalid"
        elif action == ACT_UNSUBSCRIBE and not request.subscription_id:
            error_message = 'Action "%s" requires a subscription id' % action
        else:
            error_message = None

        if error_message:
            raise StatusMessageException(
                ST_BAD_MESSAGE,
                message=error_message,
                in_response_to=request.message_id)

    @classmethod
    def handle_message(cls, service, request):

        cls.validate_request(request)

        collection = retrieve_collection(service,
                                         request.feed_name,
                                         request.message_id)

        if request.subscription_id:
            subscription = service.get_subscription(request.subscription_id)
        else:
            subscription = None

        if subscription and subscription.collection_id != collection.id:
            raise StatusMessageException(
                ST_NOT_FOUND,
                status_details={SD_ITEM: request.feed_name},
                in_response_to=request.message_id)

        response = tm10.ManageFeedSubscriptionResponse(
            message_id=cls.generate_id(),
            in_response_to=request.message_id,
            feed_name=collection.name,
            message=service.subscription_message,
        )

        results = ACTIONS[request.action](
            service=service,
            request=request,
            collection=collection,
            subscription=subscription,
            version=10)

        if not isinstance(results, (list, tuple)):
            results = [results]

        polling_services = service.get_polling_services(collection)

        for _result in results:
            instance = subscription_to_subscription_instance(
                subscription=_result,
                polling_services=polling_services,
                version=10
            )

            response.subscription_instances.append(instance)

        return response


class SubscriptionRequestHandler(BaseMessageHandler):

    supported_request_messages = [tm11.ManageCollectionSubscriptionRequest,
                                  tm10.ManageFeedSubscriptionRequest]

    @classmethod
    def handle_message(cls, service, request):

        if isinstance(request, tm10.ManageFeedSubscriptionRequest):

            return SubscriptionRequest10Handler.handle_message(
                service, request)

        elif isinstance(request, tm11.ManageCollectionSubscriptionRequest):

            return SubscriptionRequest11Handler.handle_message(
                service, request)

        else:
            raise_failure("TAXII Message not supported by message handler",
                          request.message_id)
