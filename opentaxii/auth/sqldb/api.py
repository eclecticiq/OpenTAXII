import bcrypt
import jwt
import structlog

from datetime import datetime, timedelta

from sqlalchemy import orm, engine
from sqlalchemy.orm import exc

from opentaxii.auth import OpenTAXIIAuthAPI

from . import models

__all__ = ['SQLDatabaseAPI']


SECRET = '-LONG-SECRET-STRING-'
TOKEN_TTL = 60 # min

log = structlog.getLogger(__name__)


class SQLDatabaseAPI(OpenTAXIIAuthAPI):

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


    def authenticate(self, username, password):

        try:
            account = self.Account.query.filter_by(username=username).one()
        except exc.NoResultFound:
            return

        if not account.is_password_valid(password):
            return

        return generate_token(account.id, ttl=TOKEN_TTL)


    def get_account(self, token):

        account_id = get_account_id(token)

        if not account_id:
            return

        account = self.Account.query.get(account_id)

        if not account:
            return

        return {'id' : account.id, 'username' : account.username }

    def create_account(self, username, password):

        account = self.Account(username=username)
        account.set_password(password)

        session = self.Session()
        session.add(account)
        session.commit()


def attach_all(obj, module):
    for key in module.__all__:
        if not hasattr(obj, key):
            setattr(obj, key, getattr(module, key))
    return obj


def generate_token(account_id, ttl=60):

    exp = datetime.utcnow() + timedelta(minutes=ttl)

    return jwt.encode({'account_id' : account_id, 'exp' : exp}, SECRET)


def get_account_id(token):
    try:
        payload = jwt.decode(token, SECRET)
    except jwt.InvalidTokenError:
        log.warning('Invalid token used')
        return
    except jwt.ExpiredSignatureError:
        log.warning('Expired token used')
        return

    return payload.get('account_id')

