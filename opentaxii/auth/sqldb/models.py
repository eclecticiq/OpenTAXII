import bcrypt

from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String
from sqlalchemy.ext.declarative import declarative_base

from werkzeug.security import safe_str_cmp

__all__ = ['Base', 'Account']

Base = declarative_base()

MAX_STR_LEN = 256


class Account(Base):

    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)

    username = Column(String(MAX_STR_LEN), unique=True)
    password_hash = Column(String(MAX_STR_LEN))

    def set_password(self, password):
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        self.password_hash = bcrypt.hashpw(password, bcrypt.gensalt())

    def is_password_valid(self, password):
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        hashed = self.password_hash.encode('utf-8')
        return safe_str_cmp(bcrypt.hashpw(password, hashed), hashed)
