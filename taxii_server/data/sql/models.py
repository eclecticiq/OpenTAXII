from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Table, Column, ForeignKey, Index, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.types import Integer, String, Date, DateTime, Boolean, Text, Enum

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event

from taxii_server.taxii.bindings import ContentBinding

Base = declarative_base()

from datetime import datetime
import json

__all__ = ['Base', 'InboxMessage', 'ContentBlock', 'DataCollection', 'Service']


MAX_NAME_LENGTH = 256


class Timestamped(Base):
    __abstract__ = True

    date_created = Column(DateTime, default=datetime.now)
    date_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class InboxMessage(Timestamped):

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


    def __str__(self):
        return 'InboxMessage(%s, %s)' % (self.message_id, self.date_created)


class ContentBlock(Timestamped):

    __tablename__ = 'content_blocks'

    id = Column(Integer, primary_key=True)

    message = Column(Text, nullable=True)

    timestamp_label = Column(DateTime, default=datetime.now)

    inbox_message_id = Column(Integer, ForeignKey('inbox_messages.id', onupdate="CASCADE", ondelete="CASCADE"), nullable=True)
    inbox_message = relationship('InboxMessage', backref='content_blocks')

    content = Column(Text)
    padding = Column(Text, nullable=True)

    _content_binding = Column(Text, nullable=True)

    def __init__(self, content_binding=None, **kwargs):
        super(ContentBlock, self).__init__(**kwargs)
        self.content_binding = content_binding

    @property
    def content_binding(self):
        return ContentBinding(*json.loads(self._content_binding)) if self._content_binding else None

    @content_binding.setter
    def content_binding(self, binding):
        self._content_binding = json.dumps(list(binding)) if binding else None

    def __str__(self):
        return 'ContentBlock(%s, %s, %s)' % (self.id, self.inbox_message_id, self._content_binding)



collection_to_content_block = Table('collection_to_content_block', Base.metadata,
    Column('collection_id', Integer, ForeignKey('data_collections.id')),
    Column('content_block_id', Integer, ForeignKey('content_blocks.id'))
)

service_to_collection = Table('service_to_collection', Base.metadata,
    Column('service_id', Integer, ForeignKey('services.id')),
    Column('collection_id', Integer, ForeignKey('data_collections.id'))
)


class Service(Base):

    __tablename__ = 'services'

    id = Column(String(MAX_NAME_LENGTH), primary_key=True)
    type = Column(String(MAX_NAME_LENGTH))

    _properties = Column(Text, nullable=False)

    collections = relationship('DataCollection', secondary=service_to_collection)

    @property
    def properties(self):
        return json.loads(self._properties)

    @properties.setter
    def properties(self, properties):
        self._properties = json.dumps(properties)


class DataCollection(Timestamped):

    __tablename__ = 'data_collections'

    id = Column(Integer, primary_key=True)
    name = Column(String(MAX_NAME_LENGTH))

    type = Column(String(MAX_NAME_LENGTH))
    description = Column(Text, nullable=True)

    available = Column(Boolean, default=True)
    accept_all_content = Column(Boolean, default=False)

    _supported_content = Column(Text, nullable=True)

    content_blocks = relationship('ContentBlock', secondary=collection_to_content_block)


    def __init__(self, supported_content=None, **kwargs):
        super(DataCollection, self).__init__(**kwargs)
        self.supported_content = supported_content

    @property
    def supported_content(self):
        return map(lambda x: ContentBinding(*x), json.loads(self._supported_content)) if self._supported_content else []

    @supported_content.setter
    def supported_content(self, binding):
        self._supported_content = json.dumps(binding) if binding else None

    def __str__(self):
        return u'DataCollection(%s, %s)' % (self.name, self.type)


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


