import json

from sqlalchemy import schema, types
from sqlalchemy.ext.declarative import declarative_base

from werkzeug.security import (
    check_password_hash, generate_password_hash
)

__all__ = ['Base', 'Account']

Base = declarative_base()

MAX_STR_LEN = 256
ALL_PERMISSIONS = ['read', 'modify']


class Account(Base):

    __tablename__ = 'accounts'

    id = schema.Column(types.Integer, primary_key=True)

    username = schema.Column(types.String(MAX_STR_LEN), unique=True)
    password_hash = schema.Column(types.String(MAX_STR_LEN))

    is_admin = schema.Column(types.Boolean, default=False)
    _permissions = schema.Column(types.Text, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def is_password_valid(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def permissions(self):
        return json.loads(self._permissions)

    @permissions.setter
    def permissions(self, permissions):
        for collection_name, permission in permissions.items():
            if permission not in ALL_PERMISSIONS:
                raise ValueError(
                    "Unknown permission '{}' specified for collection '{}'"
                    .format(permission, collection_name))
        self._permissions = json.dumps(permissions)
