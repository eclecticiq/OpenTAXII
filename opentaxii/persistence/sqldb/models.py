import json
from datetime import datetime

from sqlalchemy.orm import relationship
from sqlalchemy.schema import Table, Column, ForeignKey
from sqlalchemy.types import Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

__all__ = ['Base', 'ContentBlock', 'DataCollection', 'Service', 'InboxMessage', 'ResultSet', 'Subscription']

Base = declarative_base()

MAX_STR_LEN = 256


class Timestamped(Base):
    __abstract__ = True

    date_created = Column(DateTime(timezone=True), default=datetime.utcnow)

    date_updated = Column(DateTime(timezone=True), default=datetime.utcnow,
            onupdate=datetime.utcnow)


collection_to_content_block = Table('collection_to_content_block', Base.metadata,
    Column('collection_id', Integer, ForeignKey('data_collections.id')),
    Column('content_block_id', Integer, ForeignKey('content_blocks.id'))
)


class ContentBlock(Timestamped):

    __tablename__ = 'content_blocks'

    id = Column(Integer, primary_key=True)
    message = Column(Text, nullable=True)

    timestamp_label = Column(DateTime(timezone=True), default=datetime.utcnow)

    inbox_message_id = Column(Integer, ForeignKey('inbox_messages.id',
        onupdate="CASCADE", ondelete="CASCADE"), nullable=True)
    inbox_message = relationship('InboxMessage', backref='content_blocks')

    content = Column(Text)

    binding_id = Column(String(MAX_STR_LEN))
    binding_subtype = Column(String(MAX_STR_LEN))

    collections = relationship('DataCollection',
        secondary=collection_to_content_block, backref='content_blocks',
        lazy='dynamic')

    def __repr__(self):
        return 'ContentBlock(id=%s, inbox_message=%s, binding=[%s, %s])' % (
                self.id, self.inbox_message_id, self.binding_id, self.binding_subtype)


service_to_collection = Table('service_to_collection', Base.metadata,
    Column('service_id', String(MAX_STR_LEN), ForeignKey('services.id')),
    Column('collection_id', Integer, ForeignKey('data_collections.id'))
)


class Service(Timestamped):

    __tablename__ = 'services'

    id = Column(String(MAX_STR_LEN), primary_key=True)
    type = Column(String(MAX_STR_LEN))

    _properties = Column(Text, nullable=False)

    collections = relationship('DataCollection',
        secondary=service_to_collection, backref="services")

    @property
    def properties(self):
        return json.loads(self._properties)

    @properties.setter
    def properties(self, properties):
        self._properties = json.dumps(properties)


class DataCollection(Timestamped):

    __tablename__ = 'data_collections'

    id = Column(Integer, primary_key=True)
    name = Column(String(MAX_STR_LEN))

    type = Column(String(MAX_STR_LEN))
    description = Column(Text, nullable=True)

    available = Column(Boolean, default=True)
    accept_all_content = Column(Boolean, default=False)

    bindings = Column(String(MAX_STR_LEN))

    def __repr__(self):
        return u'DataCollection(%s, %s)' % (self.name, self.type)


class InboxMessage(Timestamped):

    __tablename__ = 'inbox_messages'

    id = Column(Integer, primary_key=True)

    message_id = Column(String(MAX_STR_LEN))
    result_id = Column(String(MAX_STR_LEN), nullable=True)

    record_count = Column(Integer, nullable=True)
    partial_count = Column(Boolean, default=False)

    subscription_collection_name = Column(String(MAX_STR_LEN), nullable=True)
    subscription_id = Column(String(MAX_STR_LEN), nullable=True)

    exclusive_begin_timestamp_label = Column(DateTime(timezone=True), nullable=True)
    inclusive_end_timestamp_label = Column(DateTime(timezone=True), nullable=True)

    original_message = Column(Text, nullable=False)
    content_block_count = Column(Integer)

    # FIXME: should be a proper reference ID
    destination_collections = Column(Text, nullable=True)

    service_id = Column(String(MAX_STR_LEN), ForeignKey('services.id', onupdate="CASCADE", ondelete="CASCADE"))
    service = relationship('Service', backref='inbox_messages')

    def __repr__(self):
        return 'InboxMessage(%s, %s)' % (self.message_id, self.date_created)


class ResultSet(Timestamped):

    __tablename__ = 'result_sets'

    id = Column(String(MAX_STR_LEN), primary_key=True)

    collection_id = Column(Integer, ForeignKey('data_collections.id', onupdate="CASCADE", ondelete="CASCADE"))
    collection = relationship('DataCollection', backref='result_sets')

    bindings = Column(String(MAX_STR_LEN))

    begin_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)


class Subscription(Timestamped):

    __tablename__ = 'subscriptions'

    id = Column(String(MAX_STR_LEN), primary_key=True)

    collection_id = Column(Integer, ForeignKey('data_collections.id', onupdate="CASCADE", ondelete="CASCADE"))
    collection = relationship('DataCollection', backref='subscriptions')

    params = Column(Text, nullable=True)

    # FIXME: proper enum type
    status = Column(String(MAX_STR_LEN))

    service_id = Column(String(MAX_STR_LEN), ForeignKey('services.id', onupdate="CASCADE", ondelete="CASCADE"))
    service = relationship('Service', backref='subscriptions')

