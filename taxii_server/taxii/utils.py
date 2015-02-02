import datetime
import dateutil
from dateutil.tz import tzutc

from libtaxii.constants import *

from .exceptions import StatusMessageException


def is_content_supported(supported_bindings, content_binding, version=None):

    if not hasattr(content_binding, 'binding_id') or version == 10:
        binding_id = content_binding
        subtype = None
    else:
        binding_id = content_binding.binding_id
        subtype = content_binding.subtype_ids[0] if content_binding.subtype_ids else None #FIXME: may be not the best option

    matches = [
        ((supported.binding == binding_id) and (not supported.subtypes or subtype in supported.subtypes)) \
        for supported in supported_bindings
    ]

    return any(matches)



class PollRequestProperties(object):
    """
    Holds a bunch of different items
    relating to fulfilling a PollRequest.

    It's similar to a tm11.PollRequest object,
    but holds some items specific to how
    django-taxii-services does things
    """

    def __init__(self):
        self.poll_request = None
        self.message_id = None
        self.collection = None
        self.subscription = None
        self.response_type = None
        self.content_bindings = None
        self.allow_asynch = None
        self.query = None
        self.supported_query = None
        self.exclusive_begin_timestamp_label = None
        self.inclusive_end_timestamp_label = None
        self.delivery_parameters = None

    def get_db_kwargs(self):
        kwargs = {}
        if self.collection.type == CT_DATA_FEED:
            if self.exclusive_begin_timestamp_label:
                kwargs['timestamp_label__gt'] = self.exclusive_begin_timestamp_label
            if self.inclusive_end_timestamp_label:
                kwargs['timestamp_label__lte'] = self.inclusive_end_timestamp_label
        if self.content_bindings:
            kwargs['content_binding__in'] = self.content_bindings
        return kwargs

    @staticmethod
    def from_poll_request_10(poll_service, poll_request):
        prp = PollRequestProperties()
        prp.poll_request = poll_request
        prp.message_id = poll_request.message_id
        prp.collection = poll_service.validate_collection_name(poll_request.feed_name, poll_request.message_id)

        if poll_request.subscription_id:
            try:
                s = models.Subscription.objects.get(subscription_id=poll_request.subscription_id)
                prp.subscription = s
            except models.Subscription.DoesNotExist:
                raise StatusMessageException(poll_request.message_id,
                                             ST_NOT_FOUND,
                                             status_detail={SD_ITEM: poll_request.subscription_id})
            prp.response_type = None
            prp.content_bindings = s.content_binding.all()
            prp.allow_asynch = None
            prp.delivery_parameters = s.delivery_parameters
        else:
            prp.response_type = None
            prp.content_bindings = prp.collection.get_binding_intersection_10(poll_request.content_bindings, prp.message_id)
            prp.delivery_parameters = None

        if prp.collection.type != CT_DATA_FEED:  # Only Data Feeds existed in TAXII 1.0
            raise StatusMessageException(poll_request.message_id,
                                         ST_NOT_FOUND,
                                         "The Named Data Collection is not a Data Feed, it is a Data Set. "
                                         "Only Data Feeds can be"
                                         "Polled in TAXII 1.0",
                                         {SD_ITEM: poll_request.feed_name})

        current_datetime = datetime.datetime.now(tzutc())
        # If the request specifies a timestamp label in an acceptable range, use it.
        # Otherwise, don't use a begin timestamp label
        if poll_request.exclusive_begin_timestamp_label:
            pr_ebtl = poll_request.exclusive_begin_timestamp_label
            if pr_ebtl < current_datetime:
                prp.exclusive_begin_timestamp_label = poll_request.exclusive_begin_timestamp_label

        # Use either the specified end timestamp label;
        # or the current time iff the specified end timestmap label is after the current time
        prp.inclusive_end_timestamp_label = current_datetime
        if poll_request.inclusive_end_timestamp_label:
            pr_ietl = poll_request.inclusive_end_timestamp_label
            if pr_ietl < current_datetime:
                prp.inclusive_end_timestamp_label = poll_request.inclusive_end_timestamp_label

        if ((prp.inclusive_end_timestamp_label is not None and prp.exclusive_begin_timestamp_label is not None) and
            prp.inclusive_end_timestamp_label < prp.exclusive_begin_timestamp_label):
            raise StatusMessageException(prp.message_id,
                                         ST_FAILURE,
                                         message="Invalid Timestamp Labels: End TS Label is earlier "
                                                 "than Begin TS Label")

        return prp

    @staticmethod
    def from_poll_request_11(poll_service, poll_request):
        prp = PollRequestProperties()
        prp.poll_request = poll_request
        prp.message_id = poll_request.message_id
        prp.collection = poll_service.validate_collection_name(poll_request.collection_name, poll_request.message_id)

        if poll_request.subscription_id:
            try:
                s = models.Subscription.objects.get(subscription_id=poll_request.subscription_id)
                prp.subscription = s
            except models.Subscription.DoesNotExist:
                raise StatusMessageException(poll_request.message_id,
                                             ST_NOT_FOUND,
                                             "The subscription was not found",
                                             {SD_ITEM: poll_request.subscription_id})
            prp.response_type = s.response_type
            prp.content_bindings = s.content_binding.all()
            prp.allow_asynch = False
            prp.query = s.query
            if prp.query:
                prp.supported_query = poll_service.get_supported_query(prp.query, prp.message_id)
            else:
                prp.supported_query = None
            prp.delivery_parameters = s.delivery_parameters
        else:
            pp = poll_request.poll_parameters
            prp.response_type = pp.response_type
            prp.content_bindings = prp.collection.get_binding_intersection_11(pp.content_bindings, prp.message_id)
            prp.allow_asynch = pp.allow_asynch
            prp.query = pp.query
            if prp.query:
                prp.supported_query = poll_service.get_supported_query(prp.query, prp.message_id)
            else:
                prp.supported_query = None
            prp.delivery_parameters = pp.delivery_parameters

        if prp.collection.type == CT_DATA_FEED:  # Only data feeds care about timestamp labels
            current_datetime = datetime.datetime.now(tzutc())

            # If the request specifies a timestamp label in an acceptable range, use it.
            # Otherwise, don't use a begin timestamp label
            if poll_request.exclusive_begin_timestamp_label:
                pr_ebtl = poll_request.exclusive_begin_timestamp_label
                if pr_ebtl < current_datetime:
                    prp.exclusive_begin_timestamp_label = poll_request.exclusive_begin_timestamp_label

            # Use either the specified end timestamp label;
            # or the current time iff the specified end timestmap label is after the current time
            prp.inclusive_end_timestamp_label = current_datetime
            if poll_request.inclusive_end_timestamp_label:
                pr_ietl = poll_request.inclusive_end_timestamp_label
                if pr_ietl < current_datetime:
                    prp.inclusive_end_timestamp_label = poll_request.inclusive_end_timestamp_label

            if ((prp.inclusive_end_timestamp_label is not None and prp.exclusive_begin_timestamp_label is not None) and
                prp.inclusive_end_timestamp_label < prp.exclusive_begin_timestamp_label):
                raise StatusMessageException(prp.message_id,
                                             ST_FAILURE,
                                             message="Invalid Timestamp Labels: End TS Label is earlier "
                                                     "than Begin TS Label")

        return prp
