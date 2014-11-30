from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Table, Column, ForeignKey, Index, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.types import Integer, String, Date, DateTime, Boolean, Text, Enum

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from datetime import datetime

#from importlib import import_module
#from itertools import chain
#import sys


MAX_NAME_LENGTH = 256


class Timestamped(Base):

    __abstract__ = True

    date_created = Column(DateTime, default=datetime.now)
    date_updated = Column(DateTime, onupdate=datetime.now)


class _BindingBase(Timestamped):
    """
    Base class for Bindings (e.g., Protocol Binding, Content Binding, Message Binding)
    """
    __abstract__ = True
    
    name = Column('name', String(MAX_NAME_LENGTH))
    description = Column('description', Text, nullable=True)
    binding_id = Column('binding_id', String(MAX_NAME_LENGTH), unique=True)

    def __str__(self):
        return u'%s (%s)' % (self.name, self.binding_id)


class _Tag(Base):
    """
    Not to be used by users directly. Defines common tags used for certain other models.
    """
    __abstract__ = True

    tag = Column(String(MAX_NAME_LENGTH), unique=True)
    value = Column(String(MAX_NAME_LENGTH))

    def __str__(self):
        return "%s=%s" % (self.tag, self.value)



