from typing import ClassVar, Type

from opentaxii.sqldb_helper import SQLAlchemyDB

try:
    from sqlalchemy.orm import DeclarativeMeta
except ImportError:
    from sqlalchemy.ext.declarative import DeclarativeMeta


class BaseSQLDatabaseAPI:
    BASEMODEL: ClassVar[Type[DeclarativeMeta]]

    def __init__(self, db_connection, create_tables=False, **engine_parameters):
        super().__init__()
        self.db = SQLAlchemyDB(
            db_connection,
            self.BASEMODEL,
            session_options={
                "autocommit": False,
                "autoflush": True,
            },
            **engine_parameters
        )
        if create_tables:
            self.db.create_all_tables()

    def init_app(self, app):
        self.db.init_app(app)
