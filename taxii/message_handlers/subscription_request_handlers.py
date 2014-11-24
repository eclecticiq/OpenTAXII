# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

from .base_handlers import BaseMessageHandler
from ..exceptions import StatusMessageException

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import *
from libtaxii.common import generate_message_id


class SubscriptionRequest11Handler(BaseMessageHandler):
    """
    Built-in TAXII 1.1 Manage Collection Subscription Request Handler.
    """

    supported_request_messages = [tm11.ManageCollectionSubscriptionRequest]
    version = "1"

    @staticmethod
    def unsubscribe(request, subscription=None):
        """
        Recall from the TAXII 1.1 Services Specification:
        "Attempts to unsubscribe (UNSUBSCRIBE action) where the Subscription ID does not correspond
        to an existing subscription on the named TAXII Data Collection by the identified Consumer
        SHOULD be treated as a successful attempt to unsubscribe and result in a TAXII Manage
        Collection Subscription Response without changing existing subscriptions. In other words, the
        requester is informed that there is now no subscription with that Subscription ID (even though
        there never was one in the first place)."

        Arguments:
            request (tm11.ManageCollectionSubscriptionRequest) - The request message
            subscription (models.Subscription) - The subscription to unsubscribe, \
                        can be None if there is no corresponding subscription

        Returns:
            A tm11.SubscriptionInstance (to be put in a tm11.CollectionManagementResponse

        Workflow:
            1. If the subscription exits, set the state to Unsubscribed
            2. Return a response indicating success
        """
        if subscription:
            subscription.status == SS_UNSUBSCRIBED
            subscription.save()
            si = subscription.to_subscription_instance_11()
        else:
            si = tm11.SubscriptionInstance(subscription_id=request.subscription_id,
                                           status=SS_UNSUBSCRIBED)

        return si

    @staticmethod
    def pause(request, subscription):
        """
        Workflow:
            1. Sets the subscription status to SS_PAUSED
            2. Returns `subscription.to_subscription_instance_11()`

        Arguments:
            request (tm11.ManageCollectionSubscriptionRequest) - The request message
            subscription (models.Subscription) - The subscription to unsubscribe

        Returns:
            A tm11.SubscriptionInstance object
        """
        # TODO: For pause, need to note when the pause happened so delivery of content can resume
        # later on
        subscription.status = SS_PAUSED
        subscription.save()
        return subscription.to_subscription_instance_11()

    @staticmethod
    def resume(request, subscription):
        """
        Workflow:
            1. Sets the subscription status to SS_ACTIVE
            2. Returns `subscription.to_subscription_instance_11()`

        Arguments:
            request (tm11.ManageCollectionSubscriptionRequest) - The request message
            subscription (models.Subscription) - The subscription to unsubscribe

        Returns:
            A tm11.SubscriptionInstance object
        """
        subscription.status = SS_ACTIVE
        subscription.save()
        return subscription.to_subscription_instance_11()

    @staticmethod
    def single_status(request, subscription):
        """
        Workflow:
            1. Returns `subscription.to_subscription_instance_11()`

        Arguments:
            request (tm11.ManageCollectionSubscriptionRequest) - The request message
            subscription (models.Subscription) - The subscription to unsubscribe

        Returns:
            A tm11.SubscriptionInstance object
        """
        return subscription.to_subscription_instance_11()

    @staticmethod
    def multi_status(request):
        """
        Workflow:
            1. For every subscription in the system, call `subscription.to_subscription_instance_11()`

        Arguments:
            request (tm11.ManageCollectionSubscriptionRequest) - The request message

        Returns:
            A list of tm11.SubscriptionInstance objects
        """
        subscriptions = models.Subscription.objects.all()
        subscription_list = []
        for subscription in subscriptions:
            subscription_list.append(subscription.to_subscription_instance_11())
        return subscription_list

    @staticmethod
    def subscribe(smr):
        """
        This method needs to be tested before it's
        behavior can be documented.
        """
        # TODO: Check for supported push methods (e.g., inbox protocol, delivery message binding)

        # TODO: Check for unsupported / unknown Content Bindings / Subtypes

        # Supporting all is not an error
        accept_all_content = False
        if len(smr.subscription_parameters.content_bindings) == 0:  # All bindings are supported
            accept_all_content = True

        # Iterate over specified content_bindings
        supported_contents = []
        for content_binding in smr.subscription_parameters.content_bindings:
            binding_id = content_binding.binding_id
            if len(content_binding.subtype_ids) == 0:
                # TODO: This probably needs to be in a try/catch block that returns the correct status message
                cbas = data_collection.supported_content.get(content_binding__binding_id=binding_id,
                                                             subtype__subtype_id=None)
                supported_contents.append(cbas)
            else:
                for subtype_id in content_binding.subtype_ids:
                    # TODO: This probably needs to be in a try/catch block that returns the correct status message
                    cbas = data_collection.supported_content.get(content_binding__binding_id=binding_id,
                                                                 subtype__subtype_id=subtype_id)
                    supported_contents.append(cbas)

        # TODO: Check the query format and see if it works
        # TODO: Implement query

        # 5. Attempts to create a duplicate subscription should just return the existing subscription
        subscription = models.Subscription.objects.get_or_create(response_type=smr.subscription_parameters.response_type,
                                                                 accept_all_content=accept_all_content,
                                                                 supported_content=supported_contents,  # TODO: This is probably wrong
                                                                 query=None)  # TODO: Implement query
        return subscription.to_subscription_instance_11()

    @classmethod
    def handle_message(cls, collection_management_service, manage_collection_subscription_request, django_request):
        """
        Workflow:
        (Kinda big)
        #. Validate the Data Collection that the request identifies
        #. Validate a variety of aspects of the request message
        #. If there's a subscription_id in the request message, attempt to identify that \
           subscription in the database
        #. If Action == Subscribe, call `subscribe(request)`
        #. If Action == Unsubscribe, call `unsubscribe(request, subscription)`
        #. If Action == Pause, call `pause(request, subscription)`
        #. If Action == Resume, call `resume(request, subscription)`
        #. If Action == Status and there is a `subscription_id, call single_status(request, subscription)`
        #. If Action == Status and there is not a `subscription_id, call `multi_status(request)`
        #. Return a CollectionManageSubscriptionResponse

        """
        # Create an alias because the name is long as fiddlesticks
        smr = manage_collection_subscription_request
        cms = collection_management_service

        # This code follows the guidance in the TAXII Services Spec 1.1 Section 4.4.6.
        # This code could probably be optimized, but it exists in part to be readable.

        # 1. This code doesn't do authentication, so this step is skipped

        # 2. If the Collection Name does not exist, respond with a Status Message
        data_collection = cms.validate_collection_name(smr.collection_name, smr.message_id)

        # The following code executes this truth table:
        # |Action      | Subscription ID | Subscription ID   |
        # |            |   in message?   |   DB match?       |
        # |--------------------------------------------------|
        # |Subscribe   |   Prohibited    |       N/A         |
        # |Unsubscribe |    Required     |    Not Needed     |
        # |Pause       |    Required     |     Needed        |
        # |Resume      |    Required     |     Needed        |
        # |Status      |    Optional     | Yes, if specified |

        if smr.action not in ACT_TYPES:
            raise StatusMessageException(smr.message_id,
                                         ST_BAD_MESSAGE,
                                         message="The specified value of Action was invalid.")

        # "For messages where the Action field is UNSUBSCRIBE, PAUSE, or RESUME, [subscription id] MUST be present"
        if smr.action in (ACT_UNSUBSCRIBE, ACT_PAUSE, ACT_RESUME) and not smr.subscription_id:
            raise StatusMessageException(smr.message_id,
                                         ST_BAD_MESSAGE,
                                         message="The %s action requires a subscription id." % smr.action)

        # Attempt to identify a subscription in the database
        if smr.subscription_id:
            try:
                subscription = models.Subscription.objects.get(subscription_id=request.subscription_id)
            except models.Subscription.DoesNotExist:
                subscription = None  # This is OK for certain circumstances

        # If subscription is None for Unsubscribe, that's OK, but it's not OK
        # for Pause/Resume
        if subscription is None and smr.action in (ACT_PAUSE, ACT_RESUME):
            raise StatusMessageException(smr.message_id,
                                         ST_NOT_FOUND,
                                         status_detail={SD_ITEM: smr.subscription_id})

        # Create a stub ManageCollectionSubscriptionResponse
        response = tm11.ManageCollectionSubscriptionResponse(message_id=generate_message_id(),
                                                             in_response_to=smr.message_id,
                                                             collection_name=data_collection.collection_name)

        # This code can probably be optimized
        if smr.action == ACT_SUBSCRIBE:
            subs_instance = cls.subscribe(smr)
            response.subscription_instances.append(subs_instance)
        elif smr.action == ACT_UNSUBSCRIBE:
            subs_instance = cls.subscribe(smr)
            response.subscription_instances.append(subs_instance)
        elif smr.action == ACT_PAUSE:
            subs_instance = cls.pause(smr, subscription)
            response.subscription_instances.append(subs_instance)
        elif smr.action == ACT_RESUME:
            subs_instance = cls.resume(smr, subscription)
            response.subscription_instances.append(subs_instance)
        elif smr.action == ACT_STATUS and subscription:
            subs_instance = cls.single_status(smr, subscription)
            response.subscription_instances.append(subs_instance)
        elif smr.action == ACT_STATUS and not subscription:
            subs_instances = cls.multi_status(smr)
            for subs_instance in subs_instances:
                response.subscription_instances.append(subs_instance)
        else:
            raise ValueError("Unknown Action!")

        return response


class SubscriptionRequest10Handler(BaseMessageHandler):
    """
    Built-in TAXII 1.0 Manage Collection Subscription Request Handler.
    """

    supported_request_messages = [tm10.ManageFeedSubscriptionRequest]
    version = "1"

    @staticmethod
    def handle_message(feed_management_service, manage_feed_subscription_request, django_request):
        """
        TODO: Implement this.
        """
        pass


class SubscriptionRequestHandler(BaseMessageHandler):
    """
    Built-in TAXII 1.1 and TAXII 1.0 Management Collection/Feed Subscription Request Handler.
    """

    supported_request_messages = [tm11.ManageCollectionSubscriptionRequest, tm10.ManageFeedSubscriptionRequest]
    version = "1"

    @staticmethod
    def handle_message(collection_management_service, manage_collection_subscription_request, django_request):
        """
        Passes the request to either SubscriptionRequest10Handler
        or SubscriptionRequest11Handler.
        """
        # aliases because names are long
        cms = collection_management_service
        mcsr = manage_collection_subscription_request
        dr = django_request

        if isinstance(mcsr, tm10.ManageFeedSubscriptionRequest):
            return SubscriptionRequest10Handler.handle_message(cms, mcsr, dr)
        elif isinstance(mcsr, tm11.ManageCollectionSubscriptionRequest):
            return SubscriptionRequest11Handler.handle_message(cms, mcsr, dr)
        else:
            raise StatusMessageException(mcsr.message_id,
                                         ST_FAILURE,
                                         "TAXII Message not supported by Message Handler.")
