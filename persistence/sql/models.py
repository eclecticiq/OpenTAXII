from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Table, Column, ForeignKey, Index, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.types import Integer, String, Date, DateTime, Boolean, Text, Enum

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event

Base = declarative_base()

from datetime import datetime
import json


MAX_NAME_LENGTH = 256


class Timestamped(Base):
    __abstract__ = True

    date_created = Column(DateTime, default=datetime.now)
    date_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class InboxMessage(Timestamped):
    # TODO: What should I index on?

    __tablename__ = 'inbox_messages'

    id = Column(Integer, primary_key=True)

    message_id = Column(String(MAX_NAME_LENGTH))
    sending_ip = Column(String(MAX_NAME_LENGTH))
    result_id = Column(String(MAX_NAME_LENGTH), nullable=True)

    # Record Count items
    record_count = Column(Integer, nullable=True)
    partial_count = Column(Boolean, default=False)

    # Subscription Information items
    collection_name = Column(String(MAX_NAME_LENGTH), nullable=True)
    subscription_id = Column(String(MAX_NAME_LENGTH), nullable=True)

    exclusive_begin_timestamp_label = Column(DateTime, nullable=True)
    inclusive_end_timestamp_label = Column(DateTime, nullable=True)

    #received_via = models.ForeignKey('InboxService', blank=True, null=True)

    original_message = Column(Text, nullable=False)
    content_block_count = Column(Integer)
    content_blocks_saved = Column(Integer)


    def __str__(self):
        return 'InboxMessage(%s, %s)' % (self.message_id, self.date_created)


class ContentBlock(Timestamped):

    __tablename__ = 'content_blocks'

    id = Column(Integer, primary_key=True)

    message = Column(Text, nullable=True)

    timestamp_label = Column(DateTime, default=datetime.now)

    inbox_message_id = Column(Integer, ForeignKey('inbox_messages.id', onupdate="CASCADE", ondelete="CASCADE"))
    inbox_message = relationship('InboxMessage', backref='content_blocks')

    content = Column(Text)
    padding = Column(Text, nullable=True)

    def __str__(self):
        return 'ContentBlock(%s, %s, %s)' % (self.id, self.inbox_message_id)


collection_to_content_block = Table('collection_to_content_block', Base.metadata,
    Column('collection_id', Integer, ForeignKey('data_collections.id')),
    Column('content_block_id', Integer, ForeignKey('content_blocks.id'))
)


class DataCollection(Timestamped):

    __tablename__ = 'data_collections'

    id = Column(Integer, primary_key=True)

    name = Column(String(MAX_NAME_LENGTH), unique=True)
    description = Column(Text, nullable=True)
    type = Column(String(MAX_NAME_LENGTH))
    enabled = Column(Boolean, default=True)
    accept_all_content = Column(Boolean, default=False)

    supported_content = []
    
    _supported_content = Column(Text, nullable=True)

    content_blocks = relationship('ContentBlock', secondary=collection_to_content_block)

    def is_content_supported(self, cbas):
        raise Exception("HEY")
        """
        Takes an ContentBindingAndSubtype object and determines if
        this data collection supports it.

        Decision process is:
        1. If this accepts any content, return True
        2. If this supports binding ID > (All), return True
        3. If this supports binding ID and subtype ID, return True
        4. Otherwise, return False,
        """

        return self.accept_all_content or \
                len(self.supported_content.filter(content_binding=cbas.content_binding, subtype=None)) > 0 or \
                len(self.supported_content.filter(content_binding=cbas.content_binding, subtype=cbas.subtype)) > 0


    def get_supported_content(self):
        return json.loads(self._supported_content) if self._supported_content else []

    def __str__(self):
        return u'%s(%s, %s)' % (self.__class__.__name__, self.name, self.type)


def jsonify(obj):
    return json.dumps(obj, separators=(',', ':'))

@event.listens_for(DataCollection, 'before_insert', propagate=True)
def serialize_before_insert(mapper, connection, target):
    target._supported_content = jsonify(target.supported_content) if target.supported_content else None


#class QueryScope(Timestamped):
#    """
#    Model for Query Scope
#    """
#    name = Column(String(MAX_NAME_LENGTH))
#    description = Column(Text, nullable=True)
#
#    supported_query_id = Column(Integer, ForeignKey('supported_query.id'))
#    supported_query = relationship('SupportedQuery', backref='query_scopes')
#
#    scope = Column(String(MAX_NAME_LENGTH))
#    scope_type = Column(String(MAX_NAME_LENGTH))
#
#    def __str__(self):
#        return u'%s(%s=%s)' % (self.__class__.__name__, self.name, self.scope)
#


