from collections import namedtuple

from .bindings import *
from .utils import is_content_supported, prepare_supported_content, content_bindings_intersection
from .transform import to_content_binding, to_content_bindings


class ContentBindingEntity(object):

    def __init__(self, binding, subtypes=[]):
        self.binding = binding
        self.subtypes = subtypes

    def __repr__(self):
        return "ContentBindingEntity(%s, %s)" % (self.binding, self.subtypes)
    

class CollectionEntity(object):

    TYPE_FEED = CT_DATA_FEED
    TYPE_SET = CT_DATA_SET

    def __init__(self, name, id=None, description=None, type=TYPE_FEED,
            accept_all_content=False, supported_content=[], available=True):

        self.id = id
        self.name = name
        self.available = available

        if type not in [self.TYPE_FEED, self.TYPE_SET]:
            raise ValueError('Unknown collection type "%s"' % type)

        self.type = type

        self.description = description
        self.accept_all_content = accept_all_content

        self.supported_content = []
        for content in supported_content:
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


    def as_dict(self):
        return self.__dict__


    def get_supported_content(self, version):

        if self.accept_all_content:
            return []

        return prepare_supported_content(self.supported_content, version)



    def get_matching_bindings(self, requested_bindings):

        if self.accept_all_content:
            return requested_bindings

        return content_bindings_intersection(self.supported_content, requested_bindings)


    def __repr__(self):
        return "CollectionEntity(name=%s, type=%s, supported_content=%s)" % (self.name, self.type, self.supported_content)



class ContentBlockEntity(object):

    def __init__(self, content, timestamp_label, content_binding=None, id=None,
            message=None, inbox_message_id=None):

        self.content = content

        self.id = id
        self.timestamp_label = timestamp_label
        self.content_binding = content_binding
        self.message = message
        self.inbox_message_id = inbox_message_id


    def as_dict(self):
        return self.__dict__

    def __repr__(self):
        return "ContentBlockEntity(%s)" % ", ".join(("%s=%s" % (k, v)) for k, v in sorted(self.as_dict().items()))



class InboxMessageEntity(object):

    def __init__(self, message_id, original_message, content_block_count, id=None,
            result_id=None, destination_collections=[], record_count=None,
            partial_count=False, subscription_collection_name=None, subscription_id=None,
            exclusive_begin_timestamp_label=None, inclusive_end_timestamp_label=None):

        self.id = id

        self.message_id = message_id
        self.original_message = original_message
        self.content_block_count = content_block_count

        self.destination_collections = destination_collections

        self.result_id = result_id
        self.record_count = record_count
        self.partial_count = partial_count

        self.subscription_collection_name = subscription_collection_name
        self.subscription_id = subscription_id

        self.exclusive_begin_timestamp_label = exclusive_begin_timestamp_label
        self.inclusive_end_timestamp_label = inclusive_end_timestamp_label

    def as_dict(self):
        return self.__dict__

    def __repr__(self):
        return "InboxMessageEntity(%s)" % ", ".join(("%s=%s" % (k, v)) \
                for k, v in sorted(self.as_dict().items()) if k != 'original_message')
