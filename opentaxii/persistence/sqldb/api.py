import json
import structlog
from sqlalchemy import orm, engine
from sqlalchemy import and_, or_

from opentaxii.persistence import OpenTAXIIPersistenceAPI

from . import models
from . import converters as conv

__all__ = ['SQLDatabaseAPI']

log = structlog.getLogger(__name__)


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

        self.Session = orm.scoped_session(orm.sessionmaker(autocommit=False,
            autoflush=True, bind=self.engine))

        attach_all(self, models)

        self.Base.query = self.Session.query_property()

        if create_tables:
            self.create_tables()


    def create_tables(self):
        self.Base.metadata.create_all(bind=self.engine)


    def _merge(self, obj):

        s = self.Session()
        updated = s.merge(obj)
        s.commit()
        return updated


    def get_services(self, collection_id=None):

        query = self.Service.query

        if collection_id:
            query = query.filter(self.Service.collections.any(id=collection_id))

        return map(conv.to_service_entity, query.all())
 

    def get_service(self, sid):
        s = self.Service.get(sid)
        return conv.to_service_entity(s)


    def update_service(self, entity):
        service = self.Service(id=entity.id, type=entity.type,
                properties=entity.properties)
        updated = self._merge(service)
        return conv.to_service_entity(updated)


    def create_service(self, entity):
        return self.update_service(entity)


    def get_collections(self, service_id):
        service = self.Service.query.get(service_id)
        return map(conv.to_collection_entity, service.collections)


    def get_collection(self, name, service_id):

        service = self.Service.query.get(service_id)

        for c in service.collections:
            if c.name == name:
                return conv.to_collection_entity(c)


    def _get_content_query(self, collection_id=None, start_time=None,
            end_time=None, bindings=None):

        query = self.ContentBlock.query

        if collection_id:
            query = query.filter(self.ContentBlock.collections.any(id=collection_id))

        if start_time:
            query = query.filter(self.ContentBlock.date_created > start_time)

        if end_time:
            query = query.filter(self.ContentBlock.date_created <= end_time)

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

        query = self._get_content_query(collection_id=collection_id,
                start_time=start_time, end_time=end_time,
                bindings=bindings)

        return query.count()


    def get_content_blocks(self, collection_id=None, start_time=None,
            end_time=None, bindings=None, offset=0, limit=10):

        query = self._get_content_query(collection_id=collection_id,
                start_time=start_time, end_time=end_time,
                bindings=bindings)
        
        blocks = query[offset : offset + limit]

        return map(conv.to_block_entity, blocks)


    def update_collection(self, entity):

        _bindings = conv.serialize_content_bindings(entity.supported_content)

        collection = self.DataCollection(
            id = entity.id,
            name = entity.name,
            type = entity.type,
            description = entity.description,
            available = entity.available,
            accept_all_content = entity.accept_all_content,
            bindings = _bindings
        )

        updated = self._merge(collection)

        log.debug("Collection updated", collection_id=updated.id,
                collection_name=updated.name)

        return conv.to_collection_entity(updated)


    def create_collection(self, entity):
        return self.update_collection(entity)


    def attach_collection_to_services(self, collection_id, service_ids):
        
        collection = self.DataCollection.query.get(collection_id)

        if not collection:
            raise ValueError("Can't find collection with id=%s" % collection_id)

        s = self.Session()

        for sid in service_ids:
            service = self.Service.query.get(sid)
            collection.services.append(service)

        s.add(collection)
        s.commit()

        log.debug("Collection attached", collection_id=collection.id,
                collection_name=collection.name, service_ids=service_ids)


    def create_inbox_message(self, entity):
        return self.update_inbox_message(entity)


    def update_inbox_message(self, entity):

        if entity.destination_collections:
            names = json.dumps(entity.destination_collections) 
        else:
            names = None

        message = self.InboxMessage(
            id = entity.id,
            message_id = entity.message_id,
            original_message = entity.original_message,
            content_block_count = entity.content_block_count,
            destination_collections = names,

            service_id = entity.service_id,

            result_id = entity.result_id,
            record_count = entity.record_count,
            partial_count = entity.partial_count,

            subscription_collection_name = entity.subscription_collection_name,
            subscription_id = entity.subscription_id,

            exclusive_begin_timestamp_label = entity.exclusive_begin_timestamp_label,
            inclusive_end_timestamp_label = entity.inclusive_end_timestamp_label,
        )

        updated = self._merge(message)

        return conv.to_inbox_message_entity(updated)


    def update_content_block(self, entity):

        if entity.content_binding:
            binding = entity.content_binding.binding
            subtype = entity.content_binding.subtypes[0] \
                    if entity.content_binding.subtypes else None
        else:
            binding = None
            subtype = None

        content = self.ContentBlock(
            id = entity.id,
            timestamp_label = entity.timestamp_label,
            inbox_message_id = entity.inbox_message_id,
            content = entity.content,
            binding_id = binding,
            binding_subtype = subtype
        )

        updated = self._merge(content)

        return conv.to_block_entity(updated)


    def create_content_block(self, entity, collection_ids=None,
            service_id=None):
        block = self.update_content_block(entity)

        if collection_ids:
            self._attach_content_to_collections(block, collection_ids)

        return block


    def _attach_content_to_collections(self, content_block, collection_ids):

        if not collection_ids:
            return

        content_block_id = content_block.id

        s = self.Session()
        content_block = self.ContentBlock.query.get(content_block_id)

        criteria = self.DataCollection.id.in_(collection_ids)
        collections = self.DataCollection.query.filter(criteria).all()

        if not collections:
            raise ValueError("No collections were found with ids: %s" % collection_ids)

        for collection in collections:
            collection.content_blocks.append(content_block)
            s.add(collection)

            log.debug("Content block added to collection",
                    content_block_id=content_block_id,
                    collection_id=collection.id,
                    collection_name=collection.name)

        s.commit()



    def update_result_set(self, entity):

        _bindings = conv.serialize_content_bindings(entity.content_bindings)

        result_set = self.ResultSet(
            id = entity.result_id,
            collection_id = entity.collection_id,
            bindings = _bindings,
            begin_time = entity.timeframe[0],
            end_time = entity.timeframe[1]
        )

        updated = self._merge(result_set)

        return conv.to_result_set_entity(updated)

    def create_result_set(self, entity):
        return self.update_result_set(entity)

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
                response_type = entity.params.response_type,
                content_bindings = conv.serialize_content_bindings(
                        entity.params.content_bindings)
            )
        else:
            params = {}

        subscription = self.Subscription(
            id = entity.subscription_id,
            collection_id = entity.collection_id,
            params = json.dumps(params),
            status = entity.status,
            service_id = entity.service_id
        )

        updated = self._merge(subscription)

        log.debug("Subscription updated", subscription_id=updated.id,
                collection_id=updated.collection_id, status=updated.status)

        return conv.to_subscription_entity(updated)

    def create_subscription(self, entity):
        return self.update_subscription(entity)


def attach_all(obj, module):
    for key in module.__all__:
        if not hasattr(obj, key):
            setattr(obj, key, getattr(module, key))
    return obj


