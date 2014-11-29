from collections import namedtuple

from .bindings import *
from .utils import is_content_supported

    
class DataCollectionEntity(namedtuple('DataCollectionEntity',
    ["id", "name", "description", "type", "enabled", "accept_all_content", "supported_content", "content_blocks"])):


    def is_content_supported(self, content_binding):
        if self.accept_all_content:
            return True

        return is_content_supported(self.supported_content, content_bindings)


class ContentBlockEntity(namedtuple('ContentBlockEntityFields',
    ["id", "message", "inbox_message_id", "content", "padding", "timestamp_label", "content_binding"])):


    def is_content_supported(self, content_binding):
        if self.accept_all_content:
            return True

        return is_content_supported(self.supported_content, content_bindings)


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
        #FIXME: broken
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



