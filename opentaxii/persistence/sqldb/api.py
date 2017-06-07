import json
import structlog
from sqlalchemy import func, and_, or_

from opentaxii.persistence import OpenTAXIIPersistenceAPI
from opentaxii.sqldb_helper import SQLAlchemyDB

from . import converters as conv

from .models import (
    Base, Service, ResultSet, ContentBlock,
    DataCollection, InboxMessage, Subscription)

__all__ = ['SQLDatabaseAPI']

log = structlog.getLogger(__name__)

YIELD_PER_SIZE = 100


class SQLDatabaseAPI(OpenTAXIIPersistenceAPI):
    """SQL database implementation of OpenTAXII Persistence API.

    Implementation will work with any DB supported by SQLAlchemy package.

    Note: this implementation ignores ``context.account`` and does not have
    any access rules.

    :param str db_connection: a string that indicates database dialect and
                          connection arguments that will be passed directly
                          to :func:`~sqlalchemy.engine.create_engine` method.

    :param bool create_tables=False: if True, tables will be created in the DB.
    """

    def __init__(self, db_connection, create_tables=False):

        self.db = SQLAlchemyDB(
            db_connection, Base, session_options={
                'autocommit': False, 'autoflush': True,
            })
        if create_tables:
            self.db.create_all_tables()

    def init_app(self, app):
        self.db.init_app(app)

    def get_services(self, collection_id=None):
        if collection_id:
            collection = DataCollection.query.get(collection_id)
            services = collection.services
        else:
            services = Service.query.all()
        return [conv.to_service_entity(s) for s in services]

    def get_service(self, service_id):
        return conv.to_service_entity(Service.query.get(service_id))

    def update_service(self, obj):

        service = Service.query.get(obj.id) if obj.id else None
        if service:
            service.type = obj.type
            service.properties = obj.properties
        else:
            service = Service(
                id=obj.id, type=obj.type,
                properties=obj.properties)

        service = self.db.session.add(service)
        self.db.session.commit()

        return conv.to_service_entity(service)

    def create_service(self, entity):
        return self.update_service(entity)

    def get_collections(self, service_id):
        service = Service.query.get(service_id)
        return [
            conv.to_collection_entity(c) for c in service.collections]

    def get_collection(self, name, service_id):

        collection = (
            DataCollection.query.join(Service.collections)
                                .filter(Service.id == service_id)
                                .filter(DataCollection.name == name)).first()

        if collection:
            return conv.to_collection_entity(collection)

    def _get_content_query(self, collection_id=None, start_time=None,
                           end_time=None, bindings=None, count=False):
        if count:
            query = self.db.session.query(func.count(ContentBlock.id))
        else:
            query = (ContentBlock
                     .query.order_by(ContentBlock.timestamp_label.asc()))

        if collection_id:
            query = (query.join(ContentBlock.collections)
                          .filter(DataCollection.id == collection_id))

        if start_time:
            query = query.filter(
                ContentBlock.timestamp_label > start_time)

        if end_time:
            query = query.filter(ContentBlock.timestamp_label <= end_time)

        if bindings:
            criteria = []
            for binding in bindings:
                if binding.subtypes:
                    criterion = and_(
                        ContentBlock.binding_id == binding.binding,
                        ContentBlock.binding_subtype.in_(binding.subtypes)
                    )
                else:
                    criterion = ContentBlock.binding_id == binding.binding
                criteria.append(criterion)

            query = query.filter(or_(*criteria))

        return query

    def get_content_blocks_count(self, collection_id=None, start_time=None,
                                 end_time=None, bindings=None):

        query = self._get_content_query(
            collection_id=collection_id,
            start_time=start_time,
            end_time=end_time,
            bindings=bindings,
            count=True)

        return query.scalar()

    def get_content_blocks(self, collection_id=None, start_time=None,
                           end_time=None, bindings=None, offset=0, limit=None):

        query = self._get_content_query(
            collection_id=collection_id,
            start_time=start_time,
            end_time=end_time,
            bindings=bindings)

        query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return [
            conv.to_block_entity(block)
            for block in query.yield_per(YIELD_PER_SIZE)]

    def create_collection(self, entity):

        _bindings = conv.serialize_content_bindings(entity.supported_content)

        collection = DataCollection(
            name=entity.name,
            type=entity.type,
            description=entity.description,
            available=entity.available,
            accept_all_content=entity.accept_all_content,
            bindings=_bindings
        )

        self.db.session.add(collection)
        self.db.session.commit()

        return conv.to_collection_entity(collection)

    def attach_collection_to_services(self, collection_id, service_ids):

        collection = DataCollection.query.get(collection_id)

        if not collection:
            raise ValueError("Collection with id {} does not exist"
                             .format(collection_id))

        services = Service.query.filter(Service.id.in_(service_ids))

        collection.services.extend(services)

        self.db.session.add(collection)
        self.db.session.commit()

        log.debug("collection.attached", collection=collection.id,
                  collection_name=collection.name, services=service_ids)

    def create_inbox_message(self, entity):

        if entity.destination_collections:
            names = json.dumps(entity.destination_collections)
        else:
            names = None

        begin = entity.exclusive_begin_timestamp_label
        end = entity.inclusive_end_timestamp_label

        message = InboxMessage(
            original_message=entity.original_message,
            content_block_count=entity.content_block_count,
            destination_collections=names,

            service_id=entity.service_id,

            result_id=entity.result_id,
            record_count=entity.record_count,
            partial_count=entity.partial_count,

            subscription_collection_name=entity.subscription_collection_name,
            subscription_id=entity.subscription_id,

            exclusive_begin_timestamp_label=begin,
            inclusive_end_timestamp_label=end
        )

        self.db.session.add(message)
        self.db.session.commit()

        return conv.to_inbox_message_entity(message)

    def create_content_block(self, entity, collection_ids=None,
                             service_id=None):

        if entity.content_binding:
            binding = entity.content_binding.binding
            subtype = (entity.content_binding.subtypes[0]
                       if entity.content_binding.subtypes else None)
        else:
            binding = None
            subtype = None

        content = ContentBlock(
            timestamp_label=entity.timestamp_label,
            inbox_message_id=entity.inbox_message_id,
            content=entity.content,
            binding_id=binding,
            binding_subtype=subtype
        )

        self.db.session.add(content)
        self.db.session.commit()

        if collection_ids:
            self._attach_content_to_collections(content, collection_ids)

        return conv.to_block_entity(content)

    def _attach_content_to_collections(self, content_block, collection_ids):

        if not collection_ids:
            return

        criteria = DataCollection.id.in_(collection_ids)
        new_collections = DataCollection.query.filter(criteria)

        content_block.collections.extend(new_collections)

        self.db.session.add(content_block)

        log.debug("Content block added to collections",
                  content_block=content_block.id,
                  collections=new_collections.count())

        self.db.session.commit()

    def create_result_set(self, entity):

        _bindings = conv.serialize_content_bindings(entity.content_bindings)

        result_set = ResultSet(
            id=entity.id,
            collection_id=entity.collection_id,
            bindings=_bindings,
            begin_time=entity.timeframe[0],
            end_time=entity.timeframe[1]
        )

        self.db.session.add(result_set)
        self.db.session.commit()

        return conv.to_result_set_entity(result_set)

    def get_result_set(self, result_set_id):
        result_set = ResultSet.query.get(result_set_id)
        return conv.to_result_set_entity(result_set)

    def get_subscription(self, subscription_id):
        s = Subscription.query.get(subscription_id)
        return conv.to_subscription_entity(s)

    def get_subscriptions(self, service_id):
        service = Service.query.get(service_id)
        return [
            conv.to_subscription_entity(s) for s in service.subscriptions]

    def update_subscription(self, entity):

        if entity.params:
            params = dict(
                response_type=entity.params.response_type,
                content_bindings=conv.serialize_content_bindings(
                    entity.params.content_bindings)
            )
        else:
            params = {}

        subscription = (
            Subscription.query.get(entity.subscription_id)
            if entity.subscription_id else None)

        if subscription:
            subscription.collection_id = entity.collection_id
            subscription.params = json.dumps(params)
            subscription.status = entity.status
            subscription.service_id = entity.service_id
        else:
            subscription = Subscription(
                id=entity.subscription_id,
                collection_id=entity.collection_id,
                params=json.dumps(params),
                status=entity.status,
                service_id=entity.service_id
            )

        self.db.session.add(subscription)
        self.db.session.commit()

        log.debug("subscription.updated",
                  subscription=subscription.id,
                  collection=subscription.collection_id,
                  status=subscription.status)

        return conv.to_subscription_entity(subscription)

    def create_subscription(self, entity):
        return self.update_subscription(entity)

    def delete_content_blocks(self, collection_name, start_time,
                              end_time=None):

        collection = DataCollection.query.filter_by(name=collection_name).one()

        if not collection:
            raise ValueError("Collection with name '{}' does not exist"
                             .format(collection_name))

        content_blocks_query = (
            self.db.session.query(ContentBlock.id)
                           .join(DataCollection.content_blocks)
                           .filter(DataCollection.id == collection.id)
                           .filter(ContentBlock.timestamp_label > start_time))

        if end_time:
            content_blocks_query = content_blocks_query.filter(
                ContentBlock.timestamp_label <= end_time)

        counter = (
            ContentBlock.query.filter(
                ContentBlock.id.in_(content_blocks_query.subquery()))
            .delete(synchronize_session=False))

        collection.volume = (
            self.db.session
            .query(func.count(ContentBlock.id))
            .join(ContentBlock.collections)
            .filter(DataCollection.id == collection.id)).scalar()

        self.db.session.commit()

        return counter
