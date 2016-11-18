import json
from datetime import datetime

from sqlalchemy import schema, types
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base

__all__ = ['Base', 'ContentBlock', 'DataCollection', 'Service',
           'InboxMessage', 'ResultSet', 'Subscription']

Base = declarative_base(name='Model')


class AbstractModel(Base):
    __abstract__ = True

    date_created = schema.Column(
        types.DateTime(timezone=True), default=datetime.utcnow)


collection_to_content_block = schema.Table(
    'collection_to_content_block',
    Base.metadata,
    schema.Column(
        'collection_id', types.Integer,
        schema.ForeignKey('data_collections.id')),
    schema.Column(
        'content_block_id', types.Integer,
        schema.ForeignKey('content_blocks.id'), index=True),
    schema.PrimaryKeyConstraint('collection_id', 'content_block_id')
)


class ContentBlock(AbstractModel):

    __tablename__ = 'content_blocks'

    id = schema.Column(types.Integer, primary_key=True)
    message = schema.Column(types.Text, nullable=True)

    timestamp_label = schema.Column(
        types.DateTime(timezone=True),
        default=datetime.utcnow, index=True)

    inbox_message_id = schema.Column(
        types.Integer,
        schema.ForeignKey(
            'inbox_messages.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True)

    content = schema.Column(types.Text)

    binding_id = schema.Column(types.String(300), index=True)
    binding_subtype = schema.Column(types.String(300), index=True)

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


service_to_collection = schema.Table(
    'service_to_collection',
    Base.metadata,
    schema.Column('service_id',
                  types.String(150), schema.ForeignKey('services.id')),
    schema.Column('collection_id',
                  types.Integer, schema.ForeignKey('data_collections.id')),
    schema.PrimaryKeyConstraint('service_id', 'collection_id')
)


class Service(AbstractModel):

    __tablename__ = 'services'

    id = schema.Column(types.String(150), primary_key=True)
    type = schema.Column(types.String(150))

    _properties = schema.Column(types.Text, nullable=False)

    collections = relationship(
        'DataCollection',
        secondary=service_to_collection,
        backref='services')

    date_updated = schema.Column(
        types.DateTime(timezone=True), default=datetime.utcnow)

    @property
    def properties(self):
        return json.loads(self._properties)

    @properties.setter
    def properties(self, properties):
        self._properties = json.dumps(properties)


class DataCollection(AbstractModel):

    __tablename__ = 'data_collections'

    id = schema.Column(types.Integer, primary_key=True)
    name = schema.Column(types.String(300), index=True, unique=True)
    type = schema.Column(types.String(150))
    description = schema.Column(types.Text, nullable=True)

    accept_all_content = schema.Column(types.Boolean, default=False)
    bindings = schema.Column(types.Text)

    available = schema.Column(types.Boolean, default=True)
    volume = schema.Column(types.Integer, default=0)

    def __repr__(self):
        return ('DataCollection(name={obj.name}, type={obj.type})'
                .format(obj=self))


class InboxMessage(AbstractModel):

    __tablename__ = 'inbox_messages'

    id = schema.Column(types.Integer, primary_key=True)

    message_id = schema.Column(types.Text)
    result_id = schema.Column(types.Text, nullable=True)

    record_count = schema.Column(types.Integer, nullable=True)
    partial_count = schema.Column(types.Boolean, default=False)

    subscription_collection_name = schema.Column(types.Text, nullable=True)
    subscription_id = schema.Column(types.Text, nullable=True)

    exclusive_begin_timestamp_label = schema.Column(
        types.DateTime(timezone=True), nullable=True)
    inclusive_end_timestamp_label = schema.Column(
        types.DateTime(timezone=True), nullable=True)

    original_message = schema.Column(types.Text, nullable=False)
    content_block_count = schema.Column(types.Integer)

    # FIXME: should be a proper reference ID
    destination_collections = schema.Column(types.Text, nullable=True)

    service_id = schema.Column(
        types.String(150),
        schema.ForeignKey(
            'services.id', onupdate="CASCADE", ondelete="CASCADE"))

    service = relationship('Service', backref='inbox_messages')

    def __repr__(self):
        return ('InboxMessage(id={obj.message_id}, created={obj.date_created})'
                .format(obj=self))


class ResultSet(AbstractModel):

    __tablename__ = 'result_sets'

    id = schema.Column(types.String(150), primary_key=True)

    collection_id = schema.Column(
        types.Integer,
        schema.ForeignKey(
            'data_collections.id', onupdate='CASCADE', ondelete='CASCADE'))

    collection = relationship('DataCollection', backref='result_sets')

    bindings = schema.Column(types.Text)

    begin_time = schema.Column(types.DateTime(timezone=True), nullable=True)
    end_time = schema.Column(types.DateTime(timezone=True), nullable=True)


class Subscription(AbstractModel):

    __tablename__ = 'subscriptions'

    id = schema.Column(types.String(150), primary_key=True)

    collection_id = schema.Column(
        types.Integer,
        schema.ForeignKey(
            'data_collections.id', onupdate='CASCADE', ondelete='CASCADE'))
    collection = relationship('DataCollection', backref='subscriptions')

    params = schema.Column(types.Text, nullable=True)

    # FIXME: proper enum type
    status = schema.Column(types.String(150))

    service_id = schema.Column(
        types.String(150),
        schema.ForeignKey(
            'services.id', onupdate="CASCADE", ondelete="CASCADE"))
    service = relationship('Service', backref='subscriptions')
