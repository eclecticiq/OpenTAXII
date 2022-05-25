import base64
import datetime
import json
import uuid
from functools import reduce
from typing import Dict, List, Optional, Tuple

import six
import structlog
from opentaxii.common.sqldb import BaseSQLDatabaseAPI
from opentaxii.persistence import (OpenTAXII2PersistenceAPI,
                                   OpenTAXIIPersistenceAPI)
from opentaxii.persistence.sqldb import taxii2models
from opentaxii.taxii2 import entities
from opentaxii.taxii2.utils import DATETIMEFORMAT
from sqlalchemy import and_, func, literal, or_
from sqlalchemy.orm import Query, load_only

from . import converters as conv
from .models import (Base, ContentBlock, DataCollection, InboxMessage,
                     ResultSet, Service, Subscription)

__all__ = ["SQLDatabaseAPI"]

log = structlog.getLogger(__name__)

YIELD_PER_SIZE = 100


class SQLDatabaseAPI(BaseSQLDatabaseAPI, OpenTAXIIPersistenceAPI):
    """SQL database implementation of OpenTAXII Persistence API.

    Implementation will work with any DB supported by SQLAlchemy package.

    Note: this implementation ignores ``context.account`` and does not have
    any access rules.

    :param str db_connection: a string that indicates database dialect and
                          connection arguments that will be passed directly
                          to :func:`~sqlalchemy.engine.create_engine` method.

    :param bool create_tables=False: if True, tables will be created in the DB.

    :param engine_parameters=None: if defined, these arguments would be passed to sqlalchemy.create_engine
    """

    BASEMODEL = Base

    def get_services(self, collection_id=None):
        if collection_id:
            collection = self.db.session.query(DataCollection).get(collection_id)
            services = collection.services
        else:
            services = self.db.session.query(Service).all()
        return [conv.to_service_entity(s) for s in services]

    def get_service(self, service_id):
        return conv.to_service_entity(self.db.session.query(Service).get(service_id))

    def update_service(self, obj):
        service = self.db.session.query(Service).get(obj.id) if obj.id else None
        if service:
            service.type = obj.type
            service.properties = obj.properties
        else:
            service = Service(id=obj.id, type=obj.type, properties=obj.properties)
        self.db.session.add(service)
        self.db.session.commit()
        return conv.to_service_entity(service)

    def create_service(self, entity):
        return self.update_service(entity)

    def get_collections(self, service_id=None):
        if service_id:
            service = self.db.session.query(Service).get(service_id)
            collections = service.collections
        else:
            collections = self.db.session.query(DataCollection).all()
        return [conv.to_collection_entity(c) for c in collections]

    def get_collection(self, name, service_id=None):
        if service_id:
            collection = (
                self.db.session.query(DataCollection)
                .join(Service.collections)
                .filter(Service.id == service_id)
                .filter(DataCollection.name == name)
                .one_or_none()
            )
        else:
            collection = (
                self.db.session.query(DataCollection)
                .filter(DataCollection.name == name)
                .one_or_none()
            )
        if collection:
            return conv.to_collection_entity(collection)

    def update_collection(self, entity):
        _bindings = conv.serialize_content_bindings(entity.supported_content)
        collection = self.db.session.query(DataCollection).get(entity.id)
        if not collection:
            raise ValueError("DataCollection with id {} is not found".format(entity.id))
        collection.name = entity.name
        collection.type = entity.type
        collection.description = entity.description
        collection.available = entity.available
        collection.accept_all_content = entity.accept_all_content
        collection.bindings = _bindings
        self.db.session.commit()
        return conv.to_collection_entity(collection)

    def delete_collection(self, collection_name):
        collection = (
            self.db.session.query(DataCollection)
            .filter(DataCollection.name == collection_name)
            .one()
        )
        self.db.session.delete(collection)
        self.db.session.commit()

    def delete_service(self, service_id):
        service = self.db.session.query(Service).get(service_id)
        self.db.session.delete(service)
        self.db.session.commit()

    def _get_content_query(
        self,
        collection_id=None,
        start_time=None,
        end_time=None,
        bindings=None,
        count=False,
    ):
        if count:
            query = self.db.session.query(func.count(ContentBlock.id))
        else:
            query = self.db.session.query(ContentBlock).order_by(
                ContentBlock.timestamp_label.asc()
            )

        if collection_id:
            query = query.join(ContentBlock.collections).filter(
                DataCollection.id == collection_id
            )

        if start_time:
            query = query.filter(ContentBlock.timestamp_label > start_time)

        if end_time:
            query = query.filter(ContentBlock.timestamp_label <= end_time)

        if bindings:
            criteria = []
            for binding in bindings:
                if binding.subtypes:
                    criterion = and_(
                        ContentBlock.binding_id == binding.binding,
                        ContentBlock.binding_subtype.in_(binding.subtypes),
                    )
                else:
                    criterion = ContentBlock.binding_id == binding.binding
                criteria.append(criterion)

            query = query.filter(or_(*criteria))

        return query

    def get_content_blocks_count(
        self, collection_id=None, start_time=None, end_time=None, bindings=None
    ):

        query = self._get_content_query(
            collection_id=collection_id,
            start_time=start_time,
            end_time=end_time,
            bindings=bindings,
            count=True,
        )

        return query.scalar()

    def get_content_blocks(
        self,
        collection_id=None,
        start_time=None,
        end_time=None,
        bindings=None,
        offset=0,
        limit=None,
    ):

        query = self._get_content_query(
            collection_id=collection_id,
            start_time=start_time,
            end_time=end_time,
            bindings=bindings,
        )

        query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return [
            conv.to_block_entity(block) for block in query.yield_per(YIELD_PER_SIZE)
        ]

    def create_collection(self, entity):

        _bindings = conv.serialize_content_bindings(entity.supported_content)

        collection = DataCollection(
            name=entity.name,
            type=entity.type,
            description=entity.description,
            available=entity.available,
            accept_all_content=entity.accept_all_content,
            bindings=_bindings,
        )

        self.db.session.add(collection)
        self.db.session.commit()

        return conv.to_collection_entity(collection)

    def set_collection_services(self, collection_id, service_ids):
        collection = self.db.session.query(DataCollection).get(collection_id)
        if not collection:
            raise ValueError(
                "Collection with id {} does not exist".format(collection_id)
            )
        services = (
            self.db.session.query(Service).filter(Service.id.in_(service_ids)).all()
            if service_ids
            else []
        )
        missing_services = set(service_ids) - {s.id for s in services}
        if missing_services:
            raise ValueError(
                "Services with ids {} do not exist".format(missing_services)
            )
        collection.services = services
        self.db.session.add(collection)
        self.db.session.commit()
        log.debug(
            "collection.services_set",
            id=collection.id,
            name=collection.name,
            services=service_ids,
        )

    def create_inbox_message(self, entity):

        if entity.destination_collections:
            names = json.dumps(entity.destination_collections)
        else:
            names = None

        begin = entity.exclusive_begin_timestamp_label
        end = entity.inclusive_end_timestamp_label

        content = (
            entity.original_message.encode("utf-8")
            if isinstance(entity.original_message, six.string_types)
            else entity.original_message
        )

        message = InboxMessage(
            message_id=entity.message_id,
            original_message=content,
            content_block_count=entity.content_block_count,
            destination_collections=names,
            service_id=entity.service_id,
            result_id=entity.result_id,
            record_count=entity.record_count,
            partial_count=entity.partial_count,
            subscription_collection_name=entity.subscription_collection_name,
            subscription_id=entity.subscription_id,
            exclusive_begin_timestamp_label=begin,
            inclusive_end_timestamp_label=end,
        )

        self.db.session.add(message)
        self.db.session.commit()

        return conv.to_inbox_message_entity(message)

    def create_content_block(self, entity, collection_ids=None, service_id=None):

        if entity.content_binding:
            binding = entity.content_binding.binding
            subtype = (
                entity.content_binding.subtypes[0]
                if entity.content_binding.subtypes
                else None
            )
        else:
            binding = None
            subtype = None

        content = (
            entity.content.encode("utf-8")
            if isinstance(entity.content, six.string_types)
            else entity.content
        )

        content = ContentBlock(
            timestamp_label=entity.timestamp_label,
            inbox_message_id=entity.inbox_message_id,
            content=content,
            binding_id=binding,
            binding_subtype=subtype,
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
        new_collections = self.db.session.query(DataCollection).filter(criteria)

        content_block.collections.extend(new_collections)

        self.db.session.add(content_block)

        log.debug(
            "Content block added to collections",
            content_block=content_block.id,
            collections=new_collections.count(),
        )

        self.db.session.commit()

    def create_result_set(self, entity):

        _bindings = conv.serialize_content_bindings(entity.content_bindings)

        result_set = ResultSet(
            id=entity.id,
            collection_id=entity.collection_id,
            bindings=_bindings,
            begin_time=entity.timeframe[0],
            end_time=entity.timeframe[1],
        )

        self.db.session.add(result_set)
        self.db.session.commit()

        return conv.to_result_set_entity(result_set)

    def get_result_set(self, result_set_id):
        result_set = self.db.session.query(ResultSet).get(result_set_id)
        return conv.to_result_set_entity(result_set)

    def get_subscription(self, subscription_id):
        s = self.db.session.query(Subscription).get(subscription_id)
        return conv.to_subscription_entity(s)

    def get_subscriptions(self, service_id):
        service = self.db.session.query(Service).get(service_id)
        return [conv.to_subscription_entity(s) for s in service.subscriptions]

    def update_subscription(self, entity):

        if entity.params:
            params = dict(
                response_type=entity.params.response_type,
                content_bindings=conv.serialize_content_bindings(
                    entity.params.content_bindings
                ),
            )
        else:
            params = {}

        subscription = (
            self.db.session.query(Subscription).get(entity.subscription_id)
            if entity.subscription_id
            else None
        )

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
                service_id=entity.service_id,
            )

        self.db.session.add(subscription)
        self.db.session.commit()

        log.debug(
            "subscription.updated",
            subscription=subscription.id,
            collection=subscription.collection_id,
            status=subscription.status,
        )

        return conv.to_subscription_entity(subscription)

    def create_subscription(self, entity):
        return self.update_subscription(entity)

    def delete_content_blocks(
        self, collection_name, start_time, end_time=None, with_messages=False
    ):

        collection = (
            self.db.session.query(DataCollection)
            .filter_by(name=collection_name)
            .one_or_none()
        )

        if not collection:
            raise ValueError(
                "Collection with name '{}' does not exist".format(collection_name)
            )

        content_blocks_query = (
            self.db.session.query(ContentBlock.id)
            .join(DataCollection.content_blocks)
            .filter(DataCollection.id == collection.id)
            .filter(ContentBlock.timestamp_label > start_time)
        )

        if end_time:
            content_blocks_query = content_blocks_query.filter(
                ContentBlock.timestamp_label <= end_time
            )

        inbox_messages_query = (
            self.db.session.query(InboxMessage.id)
            .join(ContentBlock, ContentBlock.inbox_message_id == InboxMessage.id)
            .filter(ContentBlock.id.in_(content_blocks_query.subquery()))
        )

        if with_messages:
            (
                self.db.session.query(InboxMessage)
                .filter(
                    InboxMessage.id.in_(
                        self.db.session.query(inbox_messages_query.subquery(name="ids"))
                    )
                )
                .delete(synchronize_session=False)
            )

        counter = (
            self.db.session.query(ContentBlock)
            .filter(
                ContentBlock.id.in_(
                    self.db.session.query(content_blocks_query.subquery(name="ids"))
                )
            )
            .delete(synchronize_session=False)
        )

        collection.volume = (
            self.db.session.query(func.count(ContentBlock.id))
            .join(ContentBlock.collections)
            .filter(DataCollection.id == collection.id)
        ).scalar()

        self.db.session.commit()

        return counter


class Taxii2SQLDatabaseAPI(BaseSQLDatabaseAPI, OpenTAXII2PersistenceAPI):
    BASEMODEL = taxii2models.Base

    @staticmethod
    def get_next_param(kwargs: Dict) -> str:
        """
        Get value for `next` based on :class:`Dict` instance.

        :param :class:`Dict` kwargs: The dict to base the `next` param on

        :return: The value to use as `next` param
        :rtype: str
        """
        return base64.b64encode(
            f"{kwargs['date_added'].isoformat()}|{kwargs['id']}".encode("utf-8")
        ).decode()

    @staticmethod
    def parse_next_param(next_param: str) -> Dict:
        """
        Parse provided `next_param` into kwargs to be used to filter stix objects.
        """
        date_added_str, obj_id = (
            base64.b64decode(next_param.encode()).decode().split("|")
        )
        date_added = datetime.datetime.strptime(
            date_added_str.split("+")[0], "%Y-%m-%dT%H:%M:%S.%f"
        ).replace(tzinfo=datetime.timezone.utc)
        return {"id": obj_id, "date_added": date_added}

    def get_api_roots(self) -> List[entities.ApiRoot]:
        query = self.db.session.query(taxii2models.ApiRoot).order_by("title")
        return [
            entities.ApiRoot(
                id=obj.id,
                default=obj.default,
                title=obj.title,
                description=obj.description,
                is_public=obj.is_public,
            )
            for obj in query.all()
        ]

    def get_api_root(self, api_root_id: str) -> Optional[entities.ApiRoot]:
        api_root = (
            self.db.session.query(taxii2models.ApiRoot)
            .filter(taxii2models.ApiRoot.id == api_root_id)
            .one_or_none()
        )
        if api_root:
            return entities.ApiRoot(
                id=api_root.id,
                default=api_root.default,
                title=api_root.title,
                description=api_root.description,
                is_public=api_root.is_public,
            )
        else:
            return None

    def add_api_root(
        self,
        title: str,
        description: Optional[str] = None,
        default: Optional[bool] = False,
        is_public: bool = False,
    ) -> entities.ApiRoot:
        """
        Add a new api root.

        :param str title: Title of the new api root
        :param str description: [Optional] Description of the new api root
        :param bool default: [Optional, False] If the new api should be the default
        :param bool is_public: whether this is a publicly readable API root

        :return: The added ApiRoot entity.
        """
        api_root = taxii2models.ApiRoot(
            title=title, description=description, default=default, is_public=is_public
        )
        self.db.session.add(api_root)
        self.db.session.commit()
        if default:
            api_root.set_default(self.db.session)
        return entities.ApiRoot(
            id=api_root.id,
            default=api_root.default,
            title=api_root.title,
            description=api_root.description,
            is_public=is_public,
        )

    def get_job_and_details(
        self, api_root_id: str, job_id: str
    ) -> Tuple[Optional[entities.Job], List[entities.JobDetail]]:
        job = (
            self.db.session.query(taxii2models.Job)
            .filter(
                taxii2models.Job.api_root_id == api_root_id,
                taxii2models.Job.id == job_id,
            )
            .one_or_none()
        )
        if job is None:
            return None, []
        job_details = (
            self.db.session.query(taxii2models.JobDetail)
            .filter(
                taxii2models.JobDetail.job_id == job_id,
            )
            .order_by(taxii2models.JobDetail.stix_id)
            .all()
        )
        return (
            entities.Job(
                id=job.id,
                api_root_id=job.api_root_id,
                status=job.status,
                request_timestamp=job.request_timestamp,
                completed_timestamp=job.completed_timestamp,
            ),
            [
                entities.JobDetail(
                    id=job_detail.id,
                    job_id=job_detail.job_id,
                    stix_id=job_detail.stix_id,
                    version=job_detail.version,
                    message=job_detail.message,
                    status=job_detail.status,
                )
                for job_detail in job_details
            ],
        )

    def job_cleanup(self) -> int:
        """
        Remove jobs that are >24h old.

        :return: The number of removed jobs.
        """
        return taxii2models.Job.cleanup(self.db.session)

    def get_collections(self, api_root_id: str) -> List[entities.Collection]:
        query = (
            self.db.session.query(taxii2models.Collection)
            .filter(taxii2models.Collection.api_root_id == api_root_id)
            .order_by(taxii2models.Collection.title)
        )
        return [
            entities.Collection(
                id=obj.id,
                api_root_id=obj.api_root_id,
                title=obj.title,
                description=obj.description,
                alias=obj.alias,
                is_public=obj.is_public,
            )
            for obj in query.all()
        ]

    def get_collection(
        self, api_root_id: str, collection_id_or_alias: str
    ) -> Optional[entities.Collection]:
        id_or_alias_filter = taxii2models.Collection.alias == collection_id_or_alias
        try:
            uuid.UUID(collection_id_or_alias)
        except ValueError:
            pass
        else:
            id_or_alias_filter |= taxii2models.Collection.id == collection_id_or_alias
        obj = (
            self.db.session.query(taxii2models.Collection)
            .filter(
                taxii2models.Collection.api_root_id == api_root_id,
                id_or_alias_filter,
            )
            .one_or_none()
        )
        if obj is None:
            return None
        return entities.Collection(
            id=obj.id,
            api_root_id=obj.api_root_id,
            title=obj.title,
            description=obj.description,
            alias=obj.alias,
            is_public=obj.is_public,
        )

    def add_collection(
        self,
        api_root_id: str,
        title: str,
        description: Optional[str] = None,
        alias: Optional[str] = None,
        is_public: bool = False,
    ) -> entities.Collection:
        """
        Add a new collection.

        :param str api_root_id: ID of the api root the new collection is part of
        :param str title: Title of the new collection
        :param str description: [Optional] Description of the new collection
        :param str alias: [Optional] Alias of the new collection
        :param bool is_public: [Optional] Whether collection should be publicly readable

        :return: The added Collection entity.
        """
        collection = taxii2models.Collection(
            api_root_id=api_root_id,
            title=title,
            description=description,
            alias=alias,
            is_public=is_public,
        )
        self.db.session.add(collection)
        self.db.session.commit()

        return entities.Collection(
            id=collection.id,
            api_root_id=collection.api_root_id,
            title=collection.title,
            description=collection.description,
            alias=collection.alias,
            is_public=collection.is_public,
        )

    def _objects_query(self, collection_id: str, ordered: bool) -> Query:
        query = self.db.session.query(taxii2models.STIXObject).filter(
            taxii2models.STIXObject.collection_id == collection_id,
        )
        if ordered:
            query = query.order_by(
                taxii2models.STIXObject.date_added, taxii2models.STIXObject.id
            )
        return query

    def _apply_added_after(
        self, query: Query, added_after: Optional[datetime.datetime] = None
    ) -> Query:
        if added_after is not None:
            query = query.filter(taxii2models.STIXObject.date_added > added_after)
        return query

    def _apply_next_kwargs(
        self, query: Query, next_kwargs: Optional[Dict] = None
    ) -> Query:
        if next_kwargs is not None:
            query = query.filter(
                (taxii2models.STIXObject.date_added > next_kwargs["date_added"])
                | (
                    (taxii2models.STIXObject.date_added == next_kwargs["date_added"])
                    & (taxii2models.STIXObject.id > next_kwargs["id"])
                )
            )
        return query

    def _apply_match_id(
        self, query: Query, match_id: Optional[List[str]] = None
    ) -> Query:
        if match_id is not None:
            query = query.filter(taxii2models.STIXObject.id.in_(match_id))
        return query

    def _apply_match_type(
        self, query: Query, match_type: Optional[List[str]] = None
    ) -> Query:
        if match_type is not None:
            query = query.filter(taxii2models.STIXObject.type.in_(match_type))
        return query

    def _apply_match_version(
        self,
        query: Query,
        collection_id: str,
        match_version: Optional[List[str]] = None,
    ) -> Query:
        if match_version is None:
            match_version = ["last"]
        if "all" in match_version:
            return query
        version_filters = []
        for value in match_version:
            if value == "first":
                min_versions_subq = (
                    self.db.session.query(
                        taxii2models.STIXObject.id,
                        func.min(taxii2models.STIXObject.version).label("min_version"),
                    )
                    .filter(
                        taxii2models.STIXObject.collection_id == collection_id,
                    )
                    .group_by(taxii2models.STIXObject.id)
                    .subquery()
                )
                min_version_pks = (
                    self.db.session.query(taxii2models.STIXObject.pk)
                    .select_from(taxii2models.STIXObject)
                    .join(
                        min_versions_subq,
                        (
                            (taxii2models.STIXObject.id == min_versions_subq.c.id)
                            & (
                                taxii2models.STIXObject.version
                                == min_versions_subq.c.min_version
                            )
                        ),
                    )
                )
                version_filters.append(taxii2models.STIXObject.pk.in_(min_version_pks))
            elif value == "last":
                max_versions_subq = (
                    self.db.session.query(
                        taxii2models.STIXObject.id,
                        func.max(taxii2models.STIXObject.version).label("max_version"),
                    )
                    .filter(
                        taxii2models.STIXObject.collection_id == collection_id,
                    )
                    .group_by(taxii2models.STIXObject.id)
                    .subquery()
                )
                max_version_pks = (
                    self.db.session.query(taxii2models.STIXObject.pk)
                    .select_from(taxii2models.STIXObject)
                    .join(
                        max_versions_subq,
                        (
                            (taxii2models.STIXObject.id == max_versions_subq.c.id)
                            & (
                                taxii2models.STIXObject.version
                                == max_versions_subq.c.max_version
                            )
                        ),
                    )
                )
                version_filters.append(taxii2models.STIXObject.pk.in_(max_version_pks))
            else:
                version_filters.append(taxii2models.STIXObject.version == value)
        query = query.filter(reduce(or_, version_filters))
        return query

    def _apply_match_spec_version(
        self, query: Query, match_spec_version: Optional[List[str]] = None
    ) -> Query:
        if match_spec_version is not None:
            query = query.filter(
                taxii2models.STIXObject.spec_version.in_(match_spec_version)
            )
        return query

    def _apply_limit(
        self, query: Query, limit: Optional[int] = None
    ) -> Tuple[Query, bool]:
        if limit is not None:
            more = limit < query.count()
            query = query.limit(limit)
        else:
            more = False
        return query, more

    def _filtered_objects_query(
        self,
        collection_id: str,
        limit: Optional[int] = None,
        added_after: Optional[datetime.datetime] = None,
        next_kwargs: Optional[Dict] = None,
        match_id: Optional[List[str]] = None,
        match_type: Optional[List[str]] = None,
        match_version: Optional[List[str]] = None,
        match_spec_version: Optional[List[str]] = None,
        ordered: Optional[bool] = True,
    ) -> Tuple[Query, bool]:
        query = self._objects_query(collection_id, ordered)
        query = self._apply_added_after(query, added_after)
        query = self._apply_next_kwargs(query, next_kwargs)
        query = self._apply_match_id(query, match_id)
        query = self._apply_match_type(query, match_type)
        query = self._apply_match_version(query, collection_id, match_version)
        query = self._apply_match_spec_version(query, match_spec_version)
        query, more = self._apply_limit(query, limit)
        return query, more

    def get_manifest(
        self,
        collection_id: str,
        limit: Optional[int] = None,
        added_after: Optional[datetime.datetime] = None,
        next_kwargs: Optional[Dict] = None,
        match_id: Optional[List[str]] = None,
        match_type: Optional[List[str]] = None,
        match_version: Optional[List[str]] = None,
        match_spec_version: Optional[List[str]] = None,
    ) -> Tuple[List[entities.ManifestRecord], bool]:
        query, more = self._filtered_objects_query(
            collection_id=collection_id,
            limit=limit,
            added_after=added_after,
            next_kwargs=next_kwargs,
            match_id=match_id,
            match_type=match_type,
            match_version=match_version,
            match_spec_version=match_spec_version,
        )
        query = query.options(
            load_only(
                taxii2models.STIXObject.id,
                taxii2models.STIXObject.date_added,
                taxii2models.STIXObject.version,
                taxii2models.STIXObject.spec_version,
            )
        )
        return (
            [
                entities.ManifestRecord(
                    id=obj.id,
                    date_added=obj.date_added,
                    version=obj.version,
                    spec_version=obj.spec_version,
                )
                for obj in query.all()
            ],
            more,
        )

    def get_objects(
        self,
        collection_id: str,
        limit: Optional[int] = None,
        added_after: Optional[datetime.datetime] = None,
        next_kwargs: Optional[Dict] = None,
        match_id: Optional[List[str]] = None,
        match_type: Optional[List[str]] = None,
        match_version: Optional[List[str]] = None,
        match_spec_version: Optional[List[str]] = None,
    ) -> Tuple[List[entities.STIXObject], bool, Optional[str]]:
        query, more = self._filtered_objects_query(
            collection_id=collection_id,
            limit=limit,
            added_after=added_after,
            next_kwargs=next_kwargs,
            match_id=match_id,
            match_type=match_type,
            match_version=match_version,
            match_spec_version=match_spec_version,
        )
        items = query.all()
        if more:
            next_param = self.get_next_param(
                {"id": items[-1].id, "date_added": items[-1].date_added}
            )
        else:
            next_param = None
        return (
            [
                entities.STIXObject(
                    id=obj.id,
                    collection_id=collection_id,
                    type=obj.type,
                    spec_version=obj.spec_version,
                    date_added=obj.date_added,
                    version=obj.version,
                    serialized_data=obj.serialized_data,
                )
                for obj in items
            ],
            more,
            next_param,
        )

    def add_objects(
        self, api_root_id: str, collection_id: str, objects: List[Dict]
    ) -> Tuple[entities.Job, List[entities.JobDetail]]:
        job = taxii2models.Job(
            api_root_id=api_root_id,
            status="pending",
            request_timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        self.db.session.add(job)
        self.db.session.commit()
        job_details = []
        for obj in objects:
            version = datetime.datetime.strptime(
                obj["modified"], DATETIMEFORMAT
            ).replace(tzinfo=datetime.timezone.utc)
            if (
                not self.db.session.query(literal(True))
                .filter(
                    self.db.session.query(taxii2models.STIXObject)
                    .filter(
                        taxii2models.STIXObject.id == obj["id"],
                        taxii2models.STIXObject.collection_id == collection_id,
                        taxii2models.STIXObject.version == version,
                    )
                    .exists()
                )
                .scalar()
            ):
                self.db.session.add(
                    taxii2models.STIXObject(
                        id=obj["id"],
                        collection_id=collection_id,
                        type=obj["id"].split("--")[0],
                        spec_version=obj["spec_version"],
                        date_added=datetime.datetime.now(datetime.timezone.utc),
                        version=version,
                        serialized_data={
                            key: value
                            for (key, value) in obj.items()
                            if key not in ["id", "type", "spec_version"]
                        },
                    )
                )
            job_detail = taxii2models.JobDetail(
                job_id=job.id,
                stix_id=obj["id"],
                version=version,
                message="",
                status="success",
            )
            job_details.append(job_detail)
            self.db.session.add(job_detail)
        job.status = "complete"
        job.completed_timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.db.session.commit()
        return (
            entities.Job(
                id=job.id,
                api_root_id=job.api_root_id,
                status=job.status,
                request_timestamp=job.request_timestamp,
                completed_timestamp=job.completed_timestamp,
            ),
            [
                entities.JobDetail(
                    id=job_detail.id,
                    job_id=job_detail.job_id,
                    stix_id=job_detail.stix_id,
                    version=job_detail.version,
                    message=job_detail.message,
                    status=job_detail.status,
                )
                for job_detail in job_details
            ],
        )

    def get_object(
        self,
        collection_id: str,
        object_id: str,
        limit: Optional[int] = None,
        added_after: Optional[datetime.datetime] = None,
        next_kwargs: Optional[Dict] = None,
        match_version: Optional[List[str]] = None,
        match_spec_version: Optional[List[str]] = None,
    ) -> Tuple[Optional[List[entities.STIXObject]], bool, Optional[str]]:
        """
        Get single object from database.

        Should return `None` when object matching object_id doesn't exist.
        """
        if (
            not self.db.session.query(literal(True))
            .filter(
                self.db.session.query(taxii2models.STIXObject)
                .filter(
                    taxii2models.STIXObject.id == object_id,
                    taxii2models.STIXObject.collection_id == collection_id,
                )
                .exists()
            )
            .scalar()
        ):
            return (None, False, None)
        query, more = self._filtered_objects_query(
            collection_id=collection_id,
            limit=limit,
            added_after=added_after,
            next_kwargs=next_kwargs,
            match_id=[object_id],
            match_version=match_version,
            match_spec_version=match_spec_version,
        )
        items = query.all()
        if more:
            next_param = self.get_next_param(
                {"id": items[-1].id, "date_added": items[-1].date_added}
            )
        else:
            next_param = None
        return (
            [
                entities.STIXObject(
                    id=obj.id,
                    collection_id=collection_id,
                    type=obj.type,
                    spec_version=obj.spec_version,
                    date_added=obj.date_added,
                    version=obj.version,
                    serialized_data=obj.serialized_data,
                )
                for obj in items
            ],
            more,
            next_param,
        )

    def delete_object(
        self,
        collection_id: str,
        object_id: str,
        match_version: Optional[List[str]] = None,
        match_spec_version: Optional[List[str]] = None,
    ) -> None:
        if match_version is None:
            match_version = ["all"]
        query, _ = self._filtered_objects_query(
            collection_id=collection_id,
            match_id=[object_id],
            match_version=match_version,
            match_spec_version=match_spec_version,
            ordered=False,
        )
        query.delete("fetch")

    def get_versions(
        self,
        collection_id: str,
        object_id: str,
        limit: Optional[int] = None,
        added_after: Optional[datetime.datetime] = None,
        next_kwargs: Optional[Dict] = None,
        match_spec_version: Optional[List[str]] = None,
    ) -> Tuple[List[entities.VersionRecord], bool]:
        """
        Get all versions of single object from database.

        Should return `None` when object matching object_id doesn't exist.
        """
        if (
            not self.db.session.query(literal(True))
            .filter(
                self.db.session.query(taxii2models.STIXObject)
                .filter(
                    taxii2models.STIXObject.id == object_id,
                    taxii2models.STIXObject.collection_id == collection_id,
                )
                .exists()
            )
            .scalar()
        ):
            return (None, False)
        query, more = self._filtered_objects_query(
            collection_id=collection_id,
            limit=limit,
            added_after=added_after,
            next_kwargs=next_kwargs,
            match_id=[object_id],
            match_version=["all"],
            match_spec_version=match_spec_version,
        )
        query = query.options(
            load_only(
                taxii2models.STIXObject.date_added,
                taxii2models.STIXObject.version,
            )
        )
        return (
            [
                entities.VersionRecord(
                    date_added=obj.date_added,
                    version=obj.version,
                )
                for obj in query.all()
            ],
            more,
        )
