import os
from tempfile import mkstemp

import pytest
from opentaxii.config import ServerConfig
from opentaxii.local import context, release_context
from opentaxii.middleware import create_app
from opentaxii.server import TAXIIServer
from opentaxii.taxii.converters import dict_to_service_entity
from opentaxii.utils import configure_logging

from fixtures import DOMAIN, SERVICES

DBTYPE = os.getenv("DBTYPE", "sqlite")
if DBTYPE == "sqlite":

    @pytest.fixture(scope="session")
    def dbconn():
        filehandle, filename = mkstemp(suffix=".db")
        os.close(filehandle)
        try:
            yield f"sqlite:///{filename}"
        finally:
            try:
                os.remove(filename)
            except FileNotFoundError:
                pass


elif DBTYPE in ("mysql", "mariadb"):
    import MySQLdb

    @pytest.fixture(scope="session")
    def dbconn():
        # drop db if exists to provide clean state at beginning
        if DBTYPE == "mysql":
            port = 3306
        elif DBTYPE == "mariadb":
            port = 3307
        yield f"mysql+mysqldb://root:@127.0.0.1:{port}/test?charset=utf8"


elif DBTYPE == "postgres":
    import platform

    if platform.python_implementation() == "PyPy":
        from psycopg2cffi import compat

        compat.register()
    import psycopg2

    @pytest.fixture(scope="session")
    def dbconn():
        yield "postgresql+psycopg2://test:test@127.0.0.1:5432/test"


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


def clean_db(dbconn):
    # drop and recreate db to provide clean state at beginning
    if DBTYPE == "sqlite":
        filename = dbconn[len("sqlite:///"):]
        os.remove(filename)
    elif DBTYPE == "postgres":
        with psycopg2.connect(
            dbname="test",
            user="test",
            password="test",
            host="127.0.0.1",
            port="5432",
        ) as pg_conn:
            with pg_conn.cursor() as pg_cur:
                pg_cur.execute(
                    "DROP SCHEMA public CASCADE;"
                    "CREATE SCHEMA public;"
                    "GRANT ALL ON SCHEMA public TO test;"
                    "GRANT ALL ON SCHEMA public TO public;"
                )
        pg_conn.close()  # pypy + psycopg2cffi needs this, doesn't close conn otherwise
    elif DBTYPE in ("mysql", "mariadb"):
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
        with MySQLdb.connect(**connection_kwargs) as mysql_conn:
            mysql_conn.query(f"DROP DATABASE IF EXISTS {dbname}")
            mysql_conn.query(
                f"CREATE DATABASE {dbname} "
                f"DEFAULT CHARACTER SET utf8 "
                f"DEFAULT COLLATE utf8_general_ci"
            )


@pytest.fixture(scope="session")
def session_taxiiserver(dbconn):
    clean_db(dbconn)
    yield TAXIIServer(prepare_test_config(dbconn))


@pytest.fixture()
def app(request, dbconn, session_taxiiserver):
    truncate = request.node.get_closest_marker("truncate") or DBTYPE == "sqlite"
    if truncate:
        yield from truncate_app(dbconn)
    else:
        yield from transaction_app(dbconn, session_taxiiserver)


def transaction_app(dbconn, taxiiserver):
    context.server = taxiiserver
    app = create_app(context.server)
    app.config["TESTING"] = True
    managers = [taxiiserver.auth] + [subserver.persistence for subserver in taxiiserver.servers]
    transactions = []
    connections = []
    sessions = []
    for manager in managers:
        connection = manager.api.db.engine.connect()
        transaction = connection.begin()
        manager.api.db.session_options["bind"] = connection
        transactions.append(transaction)
        connections.append(connection)
        sessions.append(manager.api.db.session)
    yield app
    for (transaction, connection, session, manager) in zip(transactions, connections, sessions, managers):
        transaction.rollback()
        connection.close()
        session.remove()
        manager.api.db._session = None


def truncate_app(dbconn):
    clean_db(dbconn)
    taxiiserver = TAXIIServer(prepare_test_config(dbconn))
    context.server = taxiiserver
    app = create_app(context.server)
    app.config["TESTING"] = True
    yield app


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
