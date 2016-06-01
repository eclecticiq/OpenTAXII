import jwt
import structlog

from datetime import datetime, timedelta

from sqlalchemy.orm import exc

from opentaxii.auth import OpenTAXIIAuthAPI
from opentaxii.entities import Account as AccountEntity
from opentaxii.sqldb_helper import SQLAlchemyDB

from .models import Base, Account

__all__ = ['SQLDatabaseAPI']


TOKEN_TTL = 60  # min

log = structlog.getLogger(__name__)


class SQLDatabaseAPI(OpenTAXIIAuthAPI):
    """Naive SQL database implementation of OpenTAXII Auth API.

    Implementation will work with any DB supported by SQLAlchemy package.

    :param str db_connection: a string that indicates database dialect and
                          connection arguments that will be passed directly
                          to :func:`~sqlalchemy.engine.create_engine` method.

    :param bool create_tables=False: if True, tables will be created in the DB.
    """

    def __init__(self, db_connection, create_tables=False, secret=None):

        self.db = SQLAlchemyDB(
            db_connection, Base, session_options={
                'autocommit': False, 'autoflush': True,
            })
        if create_tables:
            self.db.create_all_tables()

        if not secret:
            raise ValueError('Secret is not defined for %s.%s' % (
                self.__module__, self.__class__.__name__))

        self.secret = secret

    def init_app(self, app):
        self.db.init_app(app)

    def authenticate(self, username, password):
        try:
            account = Account.query.filter_by(username=username).one()
        except exc.NoResultFound:
            return

        if not account.is_password_valid(password):
            return

        return self._generate_token(account.id, ttl=TOKEN_TTL)

    def get_account(self, token):

        account_id = self._get_account_id(token)

        if not account_id:
            return

        account = Account.query.get(account_id)

        if not account:
            return

        return AccountEntity(id=account.id, username=account.username)

    def create_account(self, username, password):

        account = Account(username=username)
        account.set_password(password)

        self.db.session.add(account)
        self.db.session.commit()

        return AccountEntity(id=account.id, username=username)

    def _generate_token(self, account_id, ttl=TOKEN_TTL):
        exp = datetime.utcnow() + timedelta(minutes=ttl)
        return jwt.encode(
            {'account_id': account_id, 'exp': exp},
            self.secret)

    def _get_account_id(self, token):
        try:
            payload = jwt.decode(token, self.secret)
        except jwt.ExpiredSignatureError:
            log.warning('Invalid token used', token=token)
            return
        except jwt.DecodeError:
            log.warning('Can not decode a token', token=token)
            return

        return payload.get('account_id')
