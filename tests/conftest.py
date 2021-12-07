import os

import pytest
from opentaxii.config import ServerConfig
from opentaxii.local import context, release_context
from opentaxii.middleware import create_app
from opentaxii.server import TAXIIServer
from opentaxii.taxii.converters import dict_to_service_entity
from opentaxii.utils import configure_logging
from sqlalchemy import create_engine, event

from fixtures import DOMAIN, SERVICES

DBTYPE = os.getenv("DBTYPE", "sqlite")
if DBTYPE == "sqlite":

    @pytest.fixture(scope="session")
    def dbconn():
        yield "sqlite://"


elif DBTYPE in ("mysql", "mariadb"):
    import MySQLdb
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker()

    @pytest.fixture(scope="session")
    def dbconn():
        # drop db if exists to provide clean state at beginning
        dbname = "test"
        if DBTYPE == "mysql":
            port = 3306
        elif DBTYPE == "mariadb":
            port = 3307
        connection_kwargs = {
            "host": "127.0.0.1",
            "user": "root",
            "passwd": "",
            "port": port,
        }
        mysql_conn: MySQLdb.Connection = MySQLdb.connect(**connection_kwargs)
        mysql_conn.query(f"DROP DATABASE IF EXISTS {dbname}")
        mysql_conn.query(
            f"CREATE DATABASE {dbname} "
            f"DEFAULT CHARACTER SET utf8 "
            f"DEFAULT COLLATE utf8_general_ci"
        )
        mysql_conn.close()
        engine = create_engine(
            f"mysql+mysqldb://root:@127.0.0.1:{port}/test?charset=utf8",
            convert_unicode=True,
        )
        connection = engine.connect()
        yield connection
        connection.close()


elif DBTYPE == "postgres":
    import platform

    if platform.python_implementation() == "PyPy":
        from psycopg2cffi import compat

        compat.register()
    import psycopg2
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker()

    @pytest.fixture(scope="session")
    def dbconn():
        # drop public schema to provide clean state at beginning
        dbname = "test"
        pg_conn = psycopg2.connect(
            dbname=dbname,
            user="test",
            password="test",
            host="127.0.0.1",
            port="5432",
        )
        pg_cur = pg_conn.cursor()
        pg_cur.execute(
            "DROP SCHEMA public CASCADE;"
            "CREATE SCHEMA public;"
            "GRANT ALL ON SCHEMA public TO test;"
            "GRANT ALL ON SCHEMA public TO public;"
        )
        pg_cur.close()
        pg_conn.close()
        engine = create_engine(
            f"postgresql+psycopg2://test:test@127.0.0.1:5432/{dbname}",
            convert_unicode=True,
        )
        connection = engine.connect()
        yield connection
        connection.close()


else:
    raise NotImplementedError(f"dbtype {DBTYPE} not supported")


@pytest.fixture(autouse=True, scope="session")
def setup_logging():
    configure_logging({"": "debug"})


def prepare_test_config(dbconnection):
    config = ServerConfig(
        extra_configs=[
            {
                "auth_api": {
                    "class": "opentaxii.auth.sqldb.SQLDatabaseAPI",
                    "parameters": {
                        "db_connection": dbconnection,
                        "create_tables": True,
                        "secret": "dummy-secret-string-for-tests",
                    },
                },
                "taxii1": {
                    "persistence_api": {
                        "class": "opentaxii.persistence.sqldb.SQLDatabaseAPI",
                        "parameters": {
                            "db_connection": dbconnection,
                            "create_tables": True,
                        },
                    },
                },
                "taxii2": {
                    "persistence_api": {
                        "class": "opentaxii.persistence.sqldb.Taxii2SQLDatabaseAPI",
                        "parameters": {
                            "db_connection": dbconnection,
                            "create_tables": True,
                        },
                    },
                    "max_content_length": 1024,
                },
                "domain": DOMAIN,
            }
        ]
    )
    return config


@pytest.fixture
def anonymous_user():
    from opentaxii.server import anonymous_full_access

    context.account = anonymous_full_access
    yield
    release_context()


@pytest.fixture()
def app(dbconn):
    if DBTYPE != "sqlite":
        # run non-sqlite tests in nested transaction/savepoint setup to ensure atomic tests
        transaction = dbconn.begin()
        session = Session(bind=dbconn)
        session.begin_nested()

        @event.listens_for(session, "after_transaction_end")
        def restart_savepoint(session, transaction):
            if transaction.nested and not transaction._parent.nested:

                # ensure that state is expired the way
                # session.commit() at the top level normally does
                # (optional step)
                session.expire_all()

                session.begin_nested()

    context.server = TAXIIServer(prepare_test_config(dbconn))
    app = create_app(context.server)
    app.config["TESTING"] = True
    yield app
    if DBTYPE != "sqlite":
        session.close()
        transaction.rollback()


@pytest.fixture()
def server(app, anonymous_user):
    yield app.taxii_server
    release_context()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def services(server):
    for service in SERVICES:
        server.servers.taxii1.persistence.update_service(
            dict_to_service_entity(service)
        )
