"""Database models for taxii2 entities."""
import datetime
import uuid

import sqlalchemy
from opentaxii.persistence.sqldb.common import GUID, UTCDateTime
from opentaxii.taxii2 import entities
from sqlalchemy import literal
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ApiRoot(Base):
    """Database equivalent of `entities.ApiRoot`."""

    __tablename__ = "opentaxii_api_root"

    id = sqlalchemy.Column(GUID, primary_key=True, default=uuid.uuid4)
    default = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)
    title = sqlalchemy.Column(sqlalchemy.String(100), nullable=False, index=True)
    description = sqlalchemy.Column(sqlalchemy.Text)
    is_public = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

    collections = relationship("Collection", back_populates="api_root")

    def set_default(self, session: sqlalchemy.orm.Session):
        """Set this api root as default. Make sure there is always at most 1 default api root."""
        session.query(ApiRoot).filter(ApiRoot.default == literal(True)).update(
            {ApiRoot.default: literal(False)}
        )
        session.query(ApiRoot).filter(ApiRoot.id == self.id).update(
            {ApiRoot.default: literal(True)}
        )

    @classmethod
    def from_entity(cls, entity: entities.ApiRoot):
        """Generate database model from input entity."""
        return cls(**entity.to_dict())


class Job(Base):
    """Database equivalent of `entities.Job`."""

    __tablename__ = "opentaxii_job"

    id = sqlalchemy.Column(GUID, primary_key=True, default=uuid.uuid4)
    api_root_id = sqlalchemy.Column(
        GUID, sqlalchemy.ForeignKey("opentaxii_api_root.id", ondelete="CASCADE")
    )
    status = sqlalchemy.Column(
        sqlalchemy.Enum("pending", "complete", name="job_status_enum")
    )
    request_timestamp = sqlalchemy.Column(UTCDateTime, nullable=True)
    completed_timestamp = sqlalchemy.Column(UTCDateTime, nullable=True)

    details = relationship("JobDetail", back_populates="job")

    __table_args__ = (
        sqlalchemy.Index("ix_opentaxii_job_api_root_id_id", api_root_id, id),
    )

    @classmethod
    def cleanup(cls, session: sqlalchemy.orm.Session) -> int:
        """
        Remove jobs that are >24h old.

        :return: The number of removed jobs.
        """
        jobs = session.query(cls).filter(
            cls.completed_timestamp
            < (
                datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(hours=24)
            )
        )
        return jobs.delete()

    @classmethod
    def from_entity(cls, entity: entities.Job):
        """Generate database model from input entity."""
        return cls(**entity.to_dict())


class JobDetail(Base):
    """Database equivalent of `entities.JobDetail`."""

    __tablename__ = "opentaxii_job_detail"

    id = sqlalchemy.Column(GUID, primary_key=True, default=uuid.uuid4)
    job_id = sqlalchemy.Column(
        GUID, sqlalchemy.ForeignKey("opentaxii_job.id", ondelete="CASCADE"), index=True
    )
    stix_id = sqlalchemy.Column(sqlalchemy.String(100), index=True)
    version = sqlalchemy.Column(UTCDateTime)
    message = sqlalchemy.Column(sqlalchemy.Text)
    status = sqlalchemy.Column(
        sqlalchemy.Enum("success", "failure", "pending", name="job_detail_status_enum")
    )

    job = relationship("Job", back_populates="details")

    @classmethod
    def from_entity(cls, entity: entities.JobDetail):
        """Generate database model from input entity."""
        return cls(**entity.to_dict())


class Collection(Base):
    """Database equivalent of `entities.Collection`."""

    __tablename__ = "opentaxii_collection"

    id = sqlalchemy.Column(GUID, primary_key=True, default=uuid.uuid4)
    api_root_id = sqlalchemy.Column(
        GUID, sqlalchemy.ForeignKey("opentaxii_api_root.id", ondelete="CASCADE")
    )
    title = sqlalchemy.Column(sqlalchemy.String(100), nullable=False, index=True)
    description = sqlalchemy.Column(sqlalchemy.Text)
    alias = sqlalchemy.Column(sqlalchemy.String(100), nullable=True)
    is_public = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

    api_root = relationship("ApiRoot", back_populates="collections")
    objects = relationship("STIXObject", back_populates="collection")

    __table_args__ = (sqlalchemy.UniqueConstraint(api_root_id, alias),)

    @classmethod
    def from_entity(cls, entity: entities.Collection):
        """Generate database model from input entity."""
        return cls(**entity.to_dict())


class STIXObject(Base):
    """Database equivalent of `entities.STIXObject`."""

    __tablename__ = "opentaxii_stixobject"

    pk = sqlalchemy.Column(GUID, primary_key=True, default=uuid.uuid4)
    id = sqlalchemy.Column(sqlalchemy.String(100), index=True)
    collection_id = sqlalchemy.Column(
        GUID,
        sqlalchemy.ForeignKey("opentaxii_collection.id", ondelete="CASCADE"),
        index=True,
    )
    type = sqlalchemy.Column(sqlalchemy.String(50), index=True)
    spec_version = sqlalchemy.Column(sqlalchemy.String(10), index=True)  # STIX version
    date_added = sqlalchemy.Column(UTCDateTime, index=True)
    version = sqlalchemy.Column(UTCDateTime, index=True)
    serialized_data = sqlalchemy.Column(sqlalchemy.JSON)

    collection = relationship("Collection", back_populates="objects")

    __table_args__ = (
        sqlalchemy.UniqueConstraint(collection_id, id, version),
        sqlalchemy.Index("ix_opentaxii_stixobject_date_added_id", date_added, id),
    )

    @classmethod
    def from_entity(cls, entity: entities.STIXObject):
        """Generate database model from input entity."""
        return cls(**entity.to_dict())
