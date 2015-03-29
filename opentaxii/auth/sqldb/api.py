import jwt
import structlog

from datetime import datetime, timedelta

from sqlalchemy import orm, engine
from sqlalchemy.orm import exc

from opentaxii.auth import OpenTAXIIAuthAPI
from opentaxii.entities import Account

from . import models

__all__ = ['SQLDatabaseAPI']


TOKEN_TTL = 60 # min

log = structlog.getLogger(__name__)


class SQLDatabaseAPI(OpenTAXIIAuthAPI):

    def __init__(self, db_connection, create_tables=False, secret=None):

        self.engine = engine.create_engine(db_connection, convert_unicode=True)

        self.Session = orm.scoped_session(orm.sessionmaker(autocommit=False,
            autoflush=True, bind=self.engine))

        attach_all(self, models)

        self.Base.query = self.Session.query_property()

        if create_tables:
            self.create_tables()

        if not secret:
            raise ValueError('Secret is not defined for %s.%s' % (
                self.__module__, self.__class__.__name__))

        self.secret = secret


    def create_tables(self):
        self.Base.metadata.create_all(bind=self.engine)


    def authenticate(self, username, password):

        try:
            account = self.Account.query.filter_by(username=username).one()
        except exc.NoResultFound:
            return

        if not account.is_password_valid(password):
            return

        return self._generate_token(account.id, ttl=TOKEN_TTL)


    def get_account(self, token):

        account_id = self._get_account_id(token)

        if not account_id:
            return

        account = self.Account.query.get(account_id)

        if not account:
            return

        return Account(id=account.id)

    def create_account(self, username, password):

        account = self.Account(username=username)
        account.set_password(password)

        session = self.Session()
        session.add(account)
        session.commit()

        return Account(id=account.id)

    def _generate_token(self, account_id, ttl=TOKEN_TTL):

        exp = datetime.utcnow() + timedelta(minutes=ttl)

        return jwt.encode({'account_id' : account_id, 'exp' : exp}, self.secret)


    def _get_account_id(self, token):
        try:
            payload = jwt.decode(token, self.secret)
        except jwt.ExpiredSignatureError:
            log.warning('Invalid token used', token=token)
            return

        return payload.get('account_id')



def attach_all(obj, module):
    for key in module.__all__:
        if not hasattr(obj, key):
            setattr(obj, key, getattr(module, key))
    return obj


