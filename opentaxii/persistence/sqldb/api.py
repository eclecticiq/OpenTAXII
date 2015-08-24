import json
import structlog
from sqlalchemy import orm, engine, func, and_, or_

from opentaxii.persistence import OpenTAXIIPersistenceAPI

from . import models
from . import converters as conv

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

        self.engine = engine.create_engine(db_connection, convert_unicode=True)

        self.Session = orm.scoped_session(
            orm.sessionmaker(autocommit=False, autoflush=True,
                             bind=self.engine))

        attach_all(self, models)

        self.Base.query = self.Session.query_property()

        if create_tables:
            self.create_tables()

    def create_tables(self):
        self.Base.metadata.create_all(bind=self.engine)

    def get_services(self, collection_id=None):
        if collection_id:
            collection = self.DataCollection.query.get(collection_id)
            services = collection.services
        else:
            services = self.Service.query.all()
        return map(conv.to_service_entity, services)

    def get_service(self, service_id):
        return conv.to_service_entity(self.Service.get(service_id))

    def update_service(self, entity):
        service = self.Service(id=entity.id, type=entity.type,
                               properties=entity.properties)
        session = self.Session()
        service = session.merge(service)
        session.commit()
        return conv.to_service_entity(service)

    def create_service(self, entity):
        return self.update_service(entity)

    def get_collections(self, service_id):
        service = self.Service.query.get(service_id)
        return map(conv.to_collection_entity, service.collections)

    def get_collection(self, name, service_id):

        collection = (self.DataCollection.query
                                         .join(self.Service.collections)
                                         .filter(self.Service.id == service_id)
                                         .filter_by(name=name)).first()
        if collection:
            return conv.to_collection_entity(collection)

    def _get_content_query(self, collection_id=None, start_time=None,
                           end_time=None, bindings=None, count=False):
        if count:
            query = self.Session().query(func.count(self.ContentBlock.id))
        else:
            query = (self.ContentBlock
                     .query.order_by(self.ContentBlock.timestamp_label.asc()))

        if collection_id:
            query = (query.join(self.ContentBlock.collections)
                          .filter(self.DataCollection.id == collection_id))

        if start_time:
            query = query.filter(self.ContentBlock.timestamp_label > start_time)

        if end_time:
            query = query.filter(self.ContentBlock.timestamp_label <= end_time)

        if bindings:
            criteria = []
            for binding in bindings:
                if binding.subtypes:
                    criterion = and_(
                        self.ContentBlock.binding_id == binding.binding,
                        self.ContentBlock.binding_subtype.in_(binding.subtypes)
                    )
                else:
                    criterion = self.ContentBlock.binding_id == binding.binding
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

        blocks = query.yield_per(YIELD_PER_SIZE)
        return map(conv.to_block_entity, blocks.all())

    def create_collection(self, entity):

        _bindings = conv.serialize_content_bindings(entity.supported_content)

        collection = self.DataCollection(
            name=entity.name,
            type=entity.type,
            description=entity.description,
            available=entity.available,
            accept_all_content=entity.accept_all_content,
            bindings=_bindings
        )

        session = self.Session()
        session.add(collection)
        session.commit()

        log.debug("collection.created", collection_id=collection.id,
                  collection_name=collection.name)

        return conv.to_collection_entity(collection)

    def attach_collection_to_services(self, collection_id, service_ids):

        collection = self.DataCollection.query.get(collection_id)

        if not collection:
            raise ValueError("Can't find collection with id={}"
                             .format(collection_id))

        session = self.Session()

        services = self.Service.query.filter(self.Service.id.in_(service_ids))
        collection.services.extend(services)

        session.add(collection)
        session.commit()

        log.debug("Collection attached", collection_id=collection.id,
                  collection_name=collection.name, service_ids=service_ids)

    def create_inbox_message(self, entity):

        if entity.destination_collections:
            names = json.dumps(entity.destination_collections)
        else:
            names = None

        begin = entity.exclusive_begin_timestamp_label
        end = entity.inclusive_end_timestamp_label

        message = self.InboxMessage(
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

        session = self.Session()
        session.add(message)
        session.commit()

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

        content = self.ContentBlock(
            timestamp_label=entity.timestamp_label,
            inbox_message_id=entity.inbox_message_id,
            content=entity.content,
            binding_id=binding,
            binding_subtype=subtype
        )

        session = self.Session()
        session.add(content)
        session.commit()

        if collection_ids:
            self._attach_content_to_collections(content, collection_ids)

        return conv.to_block_entity(content)

    def _attach_content_to_collections(self, content_block, collection_ids):

        if not collection_ids:
            return

        criteria = self.DataCollection.id.in_(collection_ids)
        new_collections = self.DataCollection.query.filter(criteria)

        content_block.collections.extend(new_collections)

        session = self.Session()
        session.add(content_block)

        log.debug("Content block added to collections",
                  content_block_id=content_block.id,
                  collections=new_collections.count())
        session.commit()

    def create_result_set(self, entity):

        _bindings = conv.serialize_content_bindings(entity.content_bindings)

        result_set = self.ResultSet(
            id=entity.id,
            collection_id=entity.collection_id,
            bindings=_bindings,
            begin_time=entity.timeframe[0],
            end_time=entity.timeframe[1]
        )
        session = self.Session()
        session.add(result_set)
        session.commit()

        return conv.to_result_set_entity(result_set)

    def get_result_set(self, result_set_id):
        result_set = self.ResultSet.query.get(result_set_id)
        return conv.to_result_set_entity(result_set)

    def get_subscription(self, subscription_id):
        s = self.Subscription.query.get(subscription_id)
        return conv.to_subscription_entity(s)

    def get_subscriptions(self, service_id):
        service = self.Service.query.get(service_id)
        return map(conv.to_subscription_entity, service.subscriptions)

    def update_subscription(self, entity):

        if entity.params:
            params = dict(
                response_type=entity.params.response_type,
                content_bindings=conv.serialize_content_bindings(
                    entity.params.content_bindings)
            )
        else:
            params = {}

        subscription = self.Subscription(
            id=entity.subscription_id,
            collection_id=entity.collection_id,
            params=json.dumps(params),
            status=entity.status,
            service_id=entity.service_id
        )

        session = self.Session()
        subscription = session.merge(subscription)
        session.commit()

        log.debug("subscription.updated",
                  subscription=subscription.id,
                  collection=subscription.collection_id,
                  status=subscription.status)

        return conv.to_subscription_entity(subscription)

    def create_subscription(self, entity):
        return self.update_subscription(entity)


def attach_all(obj, module):
    for key in module.__all__:
        if not hasattr(obj, key):
            setattr(obj, key, getattr(module, key))
    return obj
