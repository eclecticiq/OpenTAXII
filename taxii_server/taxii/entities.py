from collections import namedtuple

from .bindings import *
from .utils import is_content_supported, prepare_supported_content

    
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
        self.supported_content = supported_content


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


    def __repr__(self):
        return "CollectionEntity(name=%s, type=%s, supported_content=%s)" % (self.name, self.type, self.supported_content)



class ContentBlockEntity(namedtuple('ContentBlockEntityFields',
    ["id", "message", "inbox_message_id", "content", "padding", "timestamp_label", "content_binding"])):


    @staticmethod
    def to_entity(content_block, inbox_message_entity=None, version=10):

        if version == 10:
            content_binding = ContentBinding(binding=content_block.content_binding, subtypes=None)
            message = None

        elif version == 11:

            content_binding = ContentBinding(
                binding = content_block.content_binding.binding_id,
                subtypes = content_block.content_binding.subtype_ids or None
            )

            message = content_block.message

        # TODO: What about signatures?

        return ContentBlockEntity(
            id = None,
            message = message,
            inbox_message_id = inbox_message_entity.id,
            content = content_block.content,
            padding = content_block.padding,
            timestamp_label = content_block.timestamp_label,
            content_binding = content_binding
        )



    @staticmethod
    def from_entity(content_block, version=10):
        if version == 10:
            content_binding = content_block.content_binding_and_subtype.content_binding.binding_id
            cb = tm10.ContentBlock(content_binding=content_binding, content=content_block.content, padding=content_block.padding)

        elif version == 11:
            content_binding = tm11.ContentBinding(content_block.content_binding_and_subtype.content_binding.binding_id)
            if content_block.content_binding_and_subtype.subtype:
                content_binding.subtype_ids.append(content_block.content_binding_and_subtype.subtype.subtype_id)
            cb = tm11.ContentBlock(content_binding=content_binding, content=content_block.content, padding=content_block.padding)

        return cb


class InboxMessageEntity(namedtuple('InboxMessageEntityFields',
    ["id", "message_id", "sending_ip", "result_id", "record_count", "partial_count",
        "collection_name", "subscription_id", "exclusive_begin_timestamp_label", "inclusive_end_timestamp_label",
        "original_message", "content_block_count"])):

    @staticmethod
    def to_entity(inbox_message, received_via=None, version=10):

        params = dict((f, None) for f in InboxMessageEntity._fields)

        params.update(dict(
            message_id = inbox_message.message_id,
            original_message = inbox_message.to_xml(), #FIXME: raw?
            content_block_count = len(inbox_message.content_blocks),
            result_id = getattr(inbox_message, "result_id", None),
        ))

        #params['received_via'] = received_via  # This is an inbox service
        #inbox_message_db.sending_ip = django_request.META.get('REMOTE_ADDR', None)

        if version == 10:

            if inbox_message.subscription_information:
                si = inbox_message.subscription_information
                params.update(dict(
                    collection_name = si.feed_name,
                    subscription_id = si.subscription_id,

                # TODO: Match up exclusive vs inclusive
                    exclusive_begin_timestamp_label = si.inclusive_begin_timestamp_label, #FIXME: ??
                    inclusive_end_timestamp_label = si.inclusive_end_timestamp_label,
                ))

        elif version == 11:

            if inbox_message.record_count:
                params['record_count'] = inbox_message.record_count.record_count
                params['partial_count'] = inbox_message.record_count.partial_count

            if inbox_message.subscription_information:
                si = inbox_message.subscription_information
                params.update(dict(
                    collection_name = si.collection_name,
                    subscription_id = si.subscription_id,

                    exclusive_begin_timestamp_label = si.exclusive_begin_timestamp_label,
                    inclusive_end_timestamp_label = si.inclusive_end_timestamp_label
                ))


        return InboxMessageEntity(**params)



