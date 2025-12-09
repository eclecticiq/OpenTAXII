from datetime import datetime, timedelta
from typing import Optional

import jwt
import structlog
from sqlalchemy.orm import exc

from opentaxii.auth import OpenTAXIIAuthAPI
from opentaxii.common.sqldb import BaseSQLDatabaseAPI
from opentaxii.entities import Account as AccountEntity

from .models import Account, Base

__all__ = ["SQLDatabaseAPI"]


log = structlog.getLogger(__name__)


class SQLDatabaseAPI(BaseSQLDatabaseAPI, OpenTAXIIAuthAPI):

    BASEMODEL = Base

    def __init__(
        self,
        db_connection: str,
        create_tables: bool = False,
        secret: Optional[str] = None,
        token_ttl_secs: Optional[int] = None,
        **engine_parameters,
    ):
        """Naive SQL database implementation of OpenTAXII Auth API.

        Implementation will work with any DB supported by SQLAlchemy package.

        :param db_connection: a string that indicates database dialect and
                            connection arguments that will be passed directly to
                            :func:`~sqlalchemy.engine.create_engine` method.
        :param create_tables=False: if True, tables will be created in the DB.
        :param secret: secret string used for token generation
        :param token_ttl_secs: TTL for JWT token, in seconds.
        :param engine_parameters=None: if defined, these arguments would be passed
            to sqlalchemy.create_engine
        """
        super().__init__(db_connection, create_tables, **engine_parameters)
        if not secret:
            raise ValueError(
                "Secret is not defined for %s.%s"
                % (self.__module__, self.__class__.__name__)
            )
        self.secret = secret
        self.token_ttl_secs = token_ttl_secs or 60 * 60  # 60min

    def authenticate(self, username: str, password: str) -> str | None:
        try:
            account = self.db.session.query(Account).filter_by(username=username).one()
        except exc.NoResultFound:
            return None
        if not account.is_password_valid(password):
            return None
        return self._generate_token(account.id, ttl=self.token_ttl_secs)

    def create_account(
        self, username: str, password: str, is_admin: bool = False
    ) -> AccountEntity:
        account = Account(  # type: ignore[misc]
            username=username, is_admin=is_admin, permissions={}
        )
        account.set_password(password)
        self.db.session.add(account)
        self.db.session.commit()
        return account_to_account_entity(account)

    def get_account(self, token: str) -> AccountEntity | None:
        account_id = self._get_account_id(token)
        if not account_id:
            return None
        account = self.db.session.query(Account).get(account_id)
        if not account:
            return None
        return account_to_account_entity(account)

    def delete_account(self, username: str):
        account = (
            self.db.session.query(Account).filter_by(username=username).one_or_none()
        )
        if account:
            self.db.session.delete(account)
            self.db.session.commit()

    def get_accounts(self):
        return [
            account_to_account_entity(account)
            for account in self.db.session.query(Account).all()
        ]

    def update_account(
        self, obj: AccountEntity, password: str | None = None
    ) -> AccountEntity:
        account = (
            self.db.session.query(Account)
            .filter_by(username=obj.username)
            .one_or_none()
        )
        if not account:
            account = Account(username=obj.username)
            self.db.session.add(account)
        if password is not None:
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
            self.secret,
            algorithm="HS256",
        )

    def _get_account_id(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            log.warning('Invalid token used', token=token)
            return
        except jwt.DecodeError:
            log.warning('Can not decode a token', token=token)
            return

        return payload.get('account_id')


def account_to_account_entity(account: Account) -> AccountEntity:
    return AccountEntity(
        id=account.id,
        username=account.username,  # type: ignore[arg-type]
        is_admin=account.is_admin,
        permissions=account.permissions,
    )
