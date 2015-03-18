from libtaxii.constants import (
    CT_DATA_FEED, CT_DATA_SET, 
    SS_ACTIVE, SS_PAUSED, SS_UNSUBSCRIBED,
    RT_FULL
)

from .utils import is_content_supported

class Entity(object):

    def __repr__(self):
        pairs = ["%s=%s" % (k, v) for k, v in sorted(self.as_dict().items())]
        return "%s(%s)" % (self.__class__.__name__, ", ".join(pairs))

    def as_dict(self):
        return self.__dict__


class ServiceEntity(Entity):

    def __init__(self, type, properties, id=None):

        self.id = id
        self.type = type
        self.properties = properties


class ContentBindingEntity(Entity):

    def __init__(self, binding, subtypes=None):
        self.binding = binding
        self.subtypes = subtypes or []


class CollectionEntity(Entity):

    TYPE_FEED = CT_DATA_FEED
    TYPE_SET = CT_DATA_SET

    def __init__(self, name, id=None, description=None, type=TYPE_FEED,
            accept_all_content=False, supported_content=None, available=True):

        self.id = id
        self.name = name
        self.available = available

        if type not in [self.TYPE_FEED, self.TYPE_SET]:
            raise ValueError('Unknown collection type "%s"' % type)

        self.type = type

        self.description = description
        self.accept_all_content = accept_all_content

        self.supported_content = []
        for content in (supported_content or []):
            if isinstance(content, basestring):
                binding = ContentBindingEntity(content)
            elif isinstance(content, tuple):
                bid, subtypes = content
                binding = ContentBindingEntity(bid, subtypes=subtypes)
            elif isinstance(content, ContentBindingEntity):
                binding = content
            else:
                raise ValueError('Unknown content binding "%s"' % content)

            self.supported_content.append(binding)


    def is_content_supported(self, content_binding):
        if self.accept_all_content:
            return True

        return is_content_supported(self.supported_content, content_binding)


    def get_matching_bindings(self, requested_bindings):
        if self.accept_all_content:
            return requested_bindings

        supported_bindings = self.supported_content

        if not supported_bindings:
            return requested_bindings

        if not requested_bindings:
            return supported_bindings

        overlap = []

        for requested in requested_bindings:
            for supported in supported_bindings:

                if requested.binding != supported.binding:
                    continue

                if not supported.subtypes:
                    overlap.append(requested)
                    continue

                if not requested.subtypes:
                    overlap.append(supported)
                    continue

                subtypes_overlap = set(supported.subtypes).intersection(requested.subtypes)

                overlap.append(ContentBindingEntity(
                    binding = requested.binding, 
                    subtypes = subtypes_overlap
                ))

        return overlap

    def __repr__(self):
        return "CollectionEntity(name=%s, type=%s, supported_content=%s)" % (
                self.name, self.type, self.supported_content)


class ContentBlockEntity(Entity):

    def __init__(self, content, timestamp_label, content_binding=None, id=None,
            message=None, inbox_message_id=None):

        self.content = content

        self.id = id
        self.timestamp_label = timestamp_label
        self.content_binding = content_binding
        self.message = message
        self.inbox_message_id = inbox_message_id


class InboxMessageEntity(Entity):

    def __init__(self, message_id, original_message, content_block_count,
            service_id, id=None, result_id=None, destination_collections=None,
            record_count=None, partial_count=False, subscription_collection_name=None,
            subscription_id=None, exclusive_begin_timestamp_label=None,
            inclusive_end_timestamp_label=None):

        self.id = id

        self.message_id = message_id
        self.original_message = original_message
        self.content_block_count = content_block_count

        self.service_id = service_id

        self.destination_collections = destination_collections or []

        self.result_id = result_id
        self.record_count = record_count
        self.partial_count = partial_count

        self.subscription_collection_name = subscription_collection_name
        self.subscription_id = subscription_id

        self.exclusive_begin_timestamp_label = exclusive_begin_timestamp_label
        self.inclusive_end_timestamp_label = inclusive_end_timestamp_label



class ResultSetEntity(Entity):

    def __init__(self, result_id, collection_id, content_bindings=None, timeframe=None):

        self.result_id = result_id

        self.collection_id = collection_id
        self.content_bindings = content_bindings or []
        self.timeframe = timeframe


class SubscriptionParameters(Entity):

    # Not supported: query

    def __init__(self, response_type=RT_FULL, content_bindings=None):

        self.response_type = response_type
        self.content_bindings = content_bindings or []


class PollRequestParametersEntity(SubscriptionParameters):

    # These fields are not supported:
    # allow_asynch
    # delivery_parameters

    def __init__(self, response_type=RT_FULL, content_bindings=None):

        super(PollRequestParametersEntity, self).__init__(
                response_type=response_type, content_bindings=content_bindings)


class SubscriptionEntity(Entity):

    ACTIVE = SS_ACTIVE
    PAUSED = SS_PAUSED
    UNSUBSCRIBED = SS_UNSUBSCRIBED

    def __init__(self, collection_id=None, subscription_id=None, status=ACTIVE,
            poll_request_params=None):

        self.subscription_id = subscription_id
        self.collection_id = collection_id
        self.params = poll_request_params
        self.status = status

