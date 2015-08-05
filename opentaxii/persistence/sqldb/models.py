import json
from datetime import datetime

from sqlalchemy.orm import relationship, validates
from sqlalchemy.schema import (
    Table, Column, ForeignKey, PrimaryKeyConstraint
)
from sqlalchemy.types import Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

__all__ = ['Base', 'ContentBlock', 'DataCollection', 'Service',
           'InboxMessage', 'ResultSet', 'Subscription']

Base = declarative_base()

MAX_STR_LEN = 256


class Timestamped(Base):
    __abstract__ = True

    date_created = Column(DateTime(timezone=True), default=datetime.utcnow)


collection_to_content_block = Table(
    'collection_to_content_block',
    Base.metadata,
    Column('collection_id', Integer, ForeignKey('data_collections.id')),
    Column('content_block_id', Integer, ForeignKey('content_blocks.id')),
    PrimaryKeyConstraint('collection_id', 'content_block_id')
)


class ContentBlock(Timestamped):

    __tablename__ = 'content_blocks'

    id = Column(Integer, primary_key=True)
    message = Column(Text, nullable=True)

    timestamp_label = Column(DateTime(timezone=True),
                             default=datetime.utcnow,
                             index=True)

    inbox_message_id = Column(Integer,
                              ForeignKey('inbox_messages.id',
                                         onupdate='CASCADE',
                                         ondelete='CASCADE'),
                              nullable=True)

    inbox_message = relationship('InboxMessage', backref='content_blocks')

    content = Column(Text)

    binding_id = Column(String(MAX_STR_LEN), index=True)
    binding_subtype = Column(String(MAX_STR_LEN), index=True)

    collections = relationship(
        'DataCollection',
        secondary=collection_to_content_block,
        backref='content_blocks',
        lazy='dynamic')

    @validates('collections', include_removes=True, include_backrefs=True)
    def _update_volume(self, key, collection, is_remove):
        if is_remove:
            collection.volume = collection.__class__.volume - 1
        else:
            collection.volume = collection.__class__.volume + 1
        return collection

    def __repr__(self):
        return ('ContentBlock(id={obj.id}, '
                'inbox_message={obj.inbox_message_id}, '
                'binding={obj.binding_subtype})').format(obj=self)


service_to_collection = Table(
    'service_to_collection',
    Base.metadata,
    Column('service_id', String(MAX_STR_LEN), ForeignKey('services.id')),
    Column('collection_id', Integer, ForeignKey('data_collections.id')),
    PrimaryKeyConstraint('service_id', 'collection_id')
)


class Service(Timestamped):

    __tablename__ = 'services'

    id = Column(String(MAX_STR_LEN), primary_key=True)
    type = Column(String(MAX_STR_LEN))

    _properties = Column(Text, nullable=False)

    collections = relationship(
        'DataCollection',
        secondary=service_to_collection,
        backref='services')

    date_updated = Column(DateTime(timezone=True), default=datetime.utcnow)

    @property
    def properties(self):
        return json.loads(self._properties)

    @properties.setter
    def properties(self, properties):
        self._properties = json.dumps(properties)


class DataCollection(Timestamped):

    __tablename__ = 'data_collections'

    id = Column(Integer, primary_key=True)
    name = Column(String(MAX_STR_LEN), index=True)

    type = Column(String(MAX_STR_LEN))
    description = Column(Text, nullable=True)

    accept_all_content = Column(Boolean, default=False)
    bindings = Column(String(MAX_STR_LEN))

    available = Column(Boolean, default=True)
    volume = Column(Integer, default=0)

    def __repr__(self):
        return ('DataCollection(name={obj.name}, type={obj.type})'
                .format(obj=self))


class InboxMessage(Timestamped):

    __tablename__ = 'inbox_messages'

    id = Column(Integer, primary_key=True)

    message_id = Column(String(MAX_STR_LEN))
    result_id = Column(String(MAX_STR_LEN), nullable=True)

    record_count = Column(Integer, nullable=True)
    partial_count = Column(Boolean, default=False)

    subscription_collection_name = Column(String(MAX_STR_LEN), nullable=True)
    subscription_id = Column(String(MAX_STR_LEN), nullable=True)

    exclusive_begin_timestamp_label = Column(DateTime(timezone=True),
                                             nullable=True)
    inclusive_end_timestamp_label = Column(DateTime(timezone=True),
                                           nullable=True)

    original_message = Column(Text, nullable=False)
    content_block_count = Column(Integer)

    # FIXME: should be a proper reference ID
    destination_collections = Column(Text, nullable=True)

    service_id = Column(
        String(MAX_STR_LEN),
        ForeignKey('services.id', onupdate="CASCADE", ondelete="CASCADE"))

    service = relationship('Service', backref='inbox_messages')

    def __repr__(self):
        return ('InboxMessage(id={obj.message_id}, created={obj.date_created})'
                .format(obj=self))


class ResultSet(Timestamped):

    __tablename__ = 'result_sets'

    id = Column(String(MAX_STR_LEN), primary_key=True)

    collection_id = Column(Integer,
                           ForeignKey('data_collections.id',
                                      onupdate='CASCADE',
                                      ondelete='CASCADE'))

    collection = relationship('DataCollection', backref='result_sets')

    bindings = Column(String(MAX_STR_LEN))

    begin_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)


class Subscription(Timestamped):

    __tablename__ = 'subscriptions'

    id = Column(String(MAX_STR_LEN), primary_key=True)

    collection_id = Column(
        Integer,
        ForeignKey('data_collections.id', onupdate='CASCADE',
                   ondelete='CASCADE'))
    collection = relationship('DataCollection', backref='subscriptions')

    params = Column(Text, nullable=True)

    # FIXME: proper enum type
    status = Column(String(MAX_STR_LEN))

    service_id = Column(
        String(MAX_STR_LEN),
        ForeignKey('services.id', onupdate="CASCADE", ondelete="CASCADE"))
    service = relationship('Service', backref='subscriptions')
