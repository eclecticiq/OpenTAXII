from typing import ClassVar, Type

from opentaxii.sqldb_helper import SQLAlchemyDB

try:
    from sqlalchemy.orm import DeclarativeMeta
except ImportError:
    from sqlalchemy.ext.declarative import DeclarativeMeta

selected_db = None


class BaseSQLDatabaseAPI:
    BASEMODEL: ClassVar[Type[DeclarativeMeta]]

    def __init__(self, db_connection, create_tables=False, **engine_parameters):
        super().__init__()
        global selected_db
        if not selected_db:
            selected_db = SQLAlchemyDB(
                db_connection,
                self.BASEMODEL,
                session_options={
                    "autocommit": False,
                    "autoflush": True,
                },
                **engine_parameters
            )
        # Use same db object in auth and taxii persistent to keep exact track of connection pools
        self.db = selected_db
        self.db.Model = self.db.extend_base_model(self.BASEMODEL)
        if create_tables:
            self.db.create_all_tables()

    def init_app(self, app):
        self.db.init_app(app)
