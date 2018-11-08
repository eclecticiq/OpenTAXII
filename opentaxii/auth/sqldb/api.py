import jwt
import structlog

from datetime import datetime, timedelta

from sqlalchemy.orm import exc

from opentaxii.auth import OpenTAXIIAuthAPI
from opentaxii.entities import Account as AccountEntity
from opentaxii.sqldb_helper import SQLAlchemyDB

from .models import Base, Account

__all__ = ['SQLDatabaseAPI']


log = structlog.getLogger(__name__)


class SQLDatabaseAPI(OpenTAXIIAuthAPI):
    """Naive SQL database implementation of OpenTAXII Auth API.

    Implementation will work with any DB supported by SQLAlchemy package.

    :param str db_connection: a string that indicates database dialect and
                          connection arguments that will be passed directly
                          to :func:`~sqlalchemy.engine.create_engine` method.
    :param bool create_tables=False: if True, tables will be created in the DB.
    :param str secret: secret string used for token generation
    :param int token_ttl_secs: TTL for JWT token, in seconds.
    :param engine_parameters=None: if defined, these arguments would be passed to sqlalchemy.create_engine
    """
    def __init__(
            self,
            db_connection,
            create_tables=False,
            secret=None,
            token_ttl_secs=None,
            **engine_parameters):

        self.db = SQLAlchemyDB(
            db_connection, Base, session_options={
                'autocommit': False, 'autoflush': True},
            **engine_parameters)
        if create_tables:
            self.db.create_all_tables()
        if not secret:
            raise ValueError('Secret is not defined for %s.%s' % (
                self.__module__, self.__class__.__name__))
        self.secret = secret
        self.token_ttl_secs = token_ttl_secs or 60 * 60  # 60min

    def init_app(self, app):
        self.db.init_app(app)

    def authenticate(self, username, password):
        try:
            account = Account.query.filter_by(username=username).one()
        except exc.NoResultFound:
            return
        if not account.is_password_valid(password):
            return
        return self._generate_token(account.id, ttl=self.token_ttl_secs)

    def get_account(self, token):
        account_id = self._get_account_id(token)
        if not account_id:
            return
        account = Account.query.get(account_id)
        if not account:
            return
        return account_to_account_entity(account)

    def delete_account(self, username):
        account = Account.query.filter_by(username=username).one_or_none()
        if account:
            self.db.session.delete(account)
            self.db.session.commit()

    def get_accounts(self):
        return [
            account_to_account_entity(account)
            for account in Account.query.all()]

    def update_account(self, obj, password):
        account = Account.query.filter_by(username=obj.username).one_or_none()
        if not account:
            account = Account(username=obj.username)
            self.db.session.add(account)
        account.set_password(password)
        account.permissions = obj.permissions
        account.is_admin = obj.is_admin
        self.db.session.commit()
        return account_to_account_entity(account)

    def _generate_token(self, account_id, ttl=None):
        ttl = ttl or self.token_ttl_secs
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


def account_to_account_entity(account):
    return AccountEntity(
        id=account.id,
        username=account.username,
        is_admin=account.is_admin,
        permissions=account.permissions)
