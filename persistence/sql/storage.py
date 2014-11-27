
import sqlalchemy
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

DB_CONNECTION_STRING = "sqlite:////Users/traut/Work/taxii-server/taxii-server.db"
#DB_CONNECTION_STRING = "sqlite:///tmp/some.db"

engine = create_engine(DB_CONNECTION_STRING, convert_unicode=True)
Session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))

from .models import *
from taxii.bindings import *

Base.query = Session.query_property()
Base.metadata.create_all(bind=engine)

class DataCollectionEntity(namedtuple('DataCollectionEntityFields',
    ["id", "name", "description", "type", "enabled", "accept_all_content", "supported_content", "content_blocks"])):

    Session = Session

    @staticmethod
    def from_model(model):
        return DataCollectionEntity(
            id = model.id,
            name = model.name,
            description = model.description,
            type = model.type,
            enabled = model.enabled,
            accept_all_content = model.accept_all_content,
            supported_content = model.get_supported_content(),
            content_blocks = model.content_blocks
        )

    @staticmethod
    def get_all():
        return map(DataCollectionEntity.from_model, DataCollection.query.all())


    def to_model(entity):
        return DataCollection(**entity._asdict())


    def save(self):
        s = self.Session()
        if self.id:
            s.merge(self.to_model())
        else:
            s.add(self.to_model())
        s.commit()


    def is_content_supported(self, content_binding):

        if self.accept_all_content:
            return True

        matches = [
            ((supported.main == content_binding.binding_id) and (not supported.subtype or supported.subtype == content_binding.subtype)) \
            for supported in self.supported_content
        ]

        return any(matches)

    def add_content_block(self, content_block_entity):
        print "Content block added to %s" % self.name



class ContentBlockEntity(namedtuple('ContentBlockEntityFields',
    ["id", "message", "inbox_message", "content", "padding", "timestamp_label", "content_binding"])):

    Session = Session

    @staticmethod
    def from_content_block(content_block, inbox_message=None, version=10):

        if version == 10:
            content_binding = ContentBinding(main=content_block.content_binding, subtype=None)
            message = None

        elif version == 11:

            binding = content_block.content_binding
            #FIXME: Can there be multiple subtypes?
            if not content_block.content_binding.subtype_ids:
                content_binding = ContentBinding(main=binding.binding_id, subtype=None)
            else:
                subtypes = content_block.content_binding.subtype_ids
                content_binding = ContentBinding(main=binding.binding_id, subtype=subtypes[0])

            message = content_block.message

        # TODO: What about signatures?

        return ContentBlockEntity(
            id = None,
            message = message,
            inbox_message = inbox_message,
            content = content_block.content,
            padding = content_block.padding,
            timestamp_label = content_block.timestamp_label,
            content_binding = content_binding
        )


class InboxMessageEntity(object):

    @staticmethod
    def from_inbox_message(inbox_message, received_via=None, version=10):

        entity = InboxMessageEntity()
        entity.message_id = inbox_message.message_id,
        #inbox_message_db.sending_ip = django_request.META.get('REMOTE_ADDR', None)

        if version == 10:

            if inbox_message.subscription_information:
                si = inbox_message.subscription_information
                entity.collection_name = si.feed_name
                entity.subscription_id = si.subscription_id

                # TODO: Match up exclusive vs inclusive
                entity.exclusive_begin_timestamp_label = si.inclusive_begin_timestamp_label #FIXME: ??
                entity.inclusive_end_timestamp_label = si.inclusive_end_timestamp_label

        elif version == 11:

            entity.result_id = inbox_message.result_id

            if inbox_message.record_count:
                entity.record_count = inbox_message.record_count.record_count
                entity.partial_count = inbox_message.record_count.partial_count

            if inbox_message.subscription_information:
                si = inbox_message.subscription_information
                entity.collection_name = si.collection_name
                entity.subscription_id = si.subscription_id

                entity.exclusive_begin_timestamp_label = si.exclusive_begin_timestamp_label
                entity.inclusive_end_timestamp_label = si.inclusive_end_timestamp_label

        entity.received_via = received_via  # This is an inbox service
        entity.original_message = inbox_message.to_xml() #FIXME: raw?
        entity.content_block_count = len(inbox_message.content_blocks)
        entity.content_blocks_saved = 0

        return entity

    def to_model(self):
        return InboxMessage(
            message_id = self.message_id,
            result_id = self.result_id,
            record_count = self.record_count,
            partial_count = self.partial_count,
            collection_name = self.collection_name,
            subscription_id = self.subscription_id,
            exclusive_begin_timestamp_label = self.exclusive_begin_timestamp_label,
            inclusive_end_timestamp_label = self.inclusive_end_timestamp_label,
            original_message = self.original_message,
            content_block_count = self.content_block_count,
            content_blocks_saved = self.content_blocks_saved,

            #received_via = self.received_via,
        )

    def save(self):
        print "saving inbox object!"

        s = self.Session()
        if self.id:
            s.merge(self.to_model())
        else:
            s.add(self.to_model())
        s.commit()


