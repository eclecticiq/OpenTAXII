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

Base = declarative_base(name='Model')


class AbstractModel(Base):
    __abstract__ = True

    date_created = Column(DateTime(timezone=True), default=datetime.utcnow)


collection_to_content_block = Table(
    'collection_to_content_block',
    Base.metadata,
    Column(
        'collection_id', Integer,
        ForeignKey('data_collections.id')),
    Column(
        'content_block_id', Integer,
        ForeignKey('content_blocks.id'), index=True),
    PrimaryKeyConstraint('collection_id', 'content_block_id')
)


class ContentBlock(AbstractModel):

    __tablename__ = 'content_blocks'

    id = Column(Integer, primary_key=True)
    message = Column(Text, nullable=True)

    timestamp_label = Column(
        DateTime(timezone=True), default=datetime.utcnow, index=True)

    inbox_message_id = Column(
        Integer,
        ForeignKey(
            'inbox_messages.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True)

    content = Column(Text)

    binding_id = Column(Text, index=True)
    binding_subtype = Column(Text, index=True)

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
    Column('service_id', String, ForeignKey('services.id')),
    Column('collection_id', Integer, ForeignKey('data_collections.id')),
    PrimaryKeyConstraint('service_id', 'collection_id')
)


class Service(AbstractModel):

    __tablename__ = 'services'

    id = Column(String, primary_key=True)
    type = Column(String)

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


class DataCollection(AbstractModel):

    __tablename__ = 'data_collections'

    id = Column(Integer, primary_key=True)
    name = Column(Text, index=True, unique=True)

    type = Column(String)
    description = Column(Text, nullable=True)

    accept_all_content = Column(Boolean, default=False)
    bindings = Column(Text)

    available = Column(Boolean, default=True)
    volume = Column(Integer, default=0)

    def __repr__(self):
        return ('DataCollection(name={obj.name}, type={obj.type})'
                .format(obj=self))


class InboxMessage(AbstractModel):

    __tablename__ = 'inbox_messages'

    id = Column(Integer, primary_key=True)

    message_id = Column(Text)
    result_id = Column(Text, nullable=True)

    record_count = Column(Integer, nullable=True)
    partial_count = Column(Boolean, default=False)

    subscription_collection_name = Column(Text, nullable=True)
    subscription_id = Column(Text, nullable=True)

    exclusive_begin_timestamp_label = Column(
        DateTime(timezone=True), nullable=True)
    inclusive_end_timestamp_label = Column(
        DateTime(timezone=True), nullable=True)

    original_message = Column(Text, nullable=False)
    content_block_count = Column(Integer)

    # FIXME: should be a proper reference ID
    destination_collections = Column(Text, nullable=True)

    service_id = Column(
        Text,
        ForeignKey('services.id', onupdate="CASCADE", ondelete="CASCADE"))

    service = relationship('Service', backref='inbox_messages')

    def __repr__(self):
        return ('InboxMessage(id={obj.message_id}, created={obj.date_created})'
                .format(obj=self))


class ResultSet(AbstractModel):

    __tablename__ = 'result_sets'

    id = Column(String, primary_key=True)

    collection_id = Column(
        Integer,
        ForeignKey(
            'data_collections.id', onupdate='CASCADE', ondelete='CASCADE'))

    collection = relationship('DataCollection', backref='result_sets')

    bindings = Column(Text)

    begin_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)


class Subscription(AbstractModel):

    __tablename__ = 'subscriptions'

    id = Column(String, primary_key=True)

    collection_id = Column(
        Integer,
        ForeignKey(
            'data_collections.id', onupdate='CASCADE', ondelete='CASCADE'))
    collection = relationship('DataCollection', backref='subscriptions')

    params = Column(Text, nullable=True)

    # FIXME: proper enum type
    status = Column(String)

    service_id = Column(
        String,
        ForeignKey('services.id', onupdate="CASCADE", ondelete="CASCADE"))
    service = relationship('Service', backref='subscriptions')
