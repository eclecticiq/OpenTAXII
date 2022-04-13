"""A module to put common database helper components."""
import uuid
from datetime import timezone

from sqlalchemy.dialects import mysql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import CHAR, DateTime, TypeDecorator


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Switch implementation based on database dialect."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        """Convert from python to database representation."""
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        """Convert from database to python representation."""
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


class UTCDateTime(TypeDecorator):
    """Platform-independent DateTime type that always stores and returns UTC."""

    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Switch implementation based on database dialect."""
        if dialect.name == 'mysql':
            return dialect.type_descriptor(mysql.DATETIME(fsp=6))
        else:
            return dialect.type_descriptor(DateTime())

    def process_bind_param(self, value, engine):
        """Convert from python to database representation."""
        if value is not None:
            return value.astimezone(timezone.utc)

    def process_result_value(self, value, engine):
        """Convert from database to python representation."""
        if value is not None:
            return value.replace(tzinfo=timezone.utc)
