import base64
import os
from tempfile import mkstemp
from unittest.mock import patch

import pytest
from flask.testing import FlaskClient
from opentaxii.config import ServerConfig
from opentaxii.local import context, release_context
from opentaxii.middleware import create_app
from opentaxii.persistence.sqldb.taxii2models import (
    ApiRoot,
    Collection,
    Job,
    JobDetail,
    STIXObject,
)
from opentaxii.server import TAXIIServer
from opentaxii.taxii.converters import dict_to_service_entity
from opentaxii.taxii.http import HTTP_AUTHORIZATION
from opentaxii.utils import configure_logging

from tests.fixtures import (
    ACCOUNT,
    COLLECTIONS_B,
    DOMAIN,
    PASSWORD,
    SERVICES,
    USERNAME,
    VALID_TOKEN,
)
from tests.taxii2.utils import API_ROOTS, COLLECTIONS, JOBS, STIX_OBJECTS


class CustomClient(FlaskClient):
    def __init__(self, *args, **kwargs):
        self.headers = kwargs.pop("headers", {})
        super().__init__(*args, **kwargs)

    def open(self, *args, **kwargs):
        headers = kwargs.pop("headers", {})
        new_headers = {**self.headers, **headers}
        if new_headers:
            kwargs["headers"] = new_headers
        return super().open(*args, **kwargs)


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
        filename = dbconn[len("sqlite:///") :]
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
    managers = [taxiiserver.auth] + [
        subserver.persistence for subserver in taxiiserver.servers
    ]
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
    for transaction, connection, session, manager in zip(
        transactions, connections, sessions, managers
    ):
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
    taxiiserver.servers.taxii1.persistence.api.db.engine.dispose()
    taxiiserver.servers.taxii2.persistence.api.db.engine.dispose()


@pytest.fixture()
def taxii2_sqldb_api(app):
    yield app.taxii_server.servers.taxii2.persistence.api


@pytest.fixture()
def server(app, anonymous_user):
    yield app.taxii_server
    release_context()


@pytest.fixture()
def client(app):
    app.test_client_class = CustomClient
    return app.test_client()


def basic_auth_token(username, password):
    return base64.b64encode("{}:{}".format(username, password).encode("utf-8"))


def MOCK_AUTHENTICATE(username, password):
    if username == USERNAME and password == PASSWORD:
        return VALID_TOKEN
    return None


def MOCK_GET_ACCOUNT(token):
    if token == VALID_TOKEN:
        return ACCOUNT
    return None


@pytest.fixture()
def authenticated_client(client):
    basic_auth_header = "Basic {}".format(
        basic_auth_token(USERNAME, PASSWORD).decode("utf-8")
    )
    headers = {
        HTTP_AUTHORIZATION: basic_auth_header,
    }
    client.headers = headers
    client.account = ACCOUNT
    with (
        patch.object(
            client.application.taxii_server.auth.api,
            "authenticate",
            side_effect=MOCK_AUTHENTICATE,
        ),
        patch.object(
            client.application.taxii_server.auth.api,
            "get_account",
            side_effect=MOCK_GET_ACCOUNT,
        ),
    ):
        yield client


@pytest.fixture()
def services(server):
    for service in SERVICES:
        server.servers.taxii1.persistence.update_service(
            dict_to_service_entity(service)
        )


@pytest.fixture()
def collections(server):
    for collection in COLLECTIONS_B:
        server.servers.taxii1.persistence.create_collection(collection)


@pytest.fixture()
def account(server):
    server.auth.api.create_account(ACCOUNT.username, "mypass")


@pytest.fixture(scope="function")
def db_api_roots(request, taxii2_sqldb_api):
    try:
        api_roots = request.param
    except AttributeError:
        api_roots = API_ROOTS
    for api_root in api_roots:
        taxii2_sqldb_api.db.session.add(ApiRoot.from_entity(api_root))
    taxii2_sqldb_api.db.session.commit()
    yield api_roots


@pytest.fixture(scope="function")
def db_jobs(request, taxii2_sqldb_api, db_api_roots):
    try:
        jobs = request.param
    except AttributeError:
        jobs = JOBS
    for job in jobs:
        taxii2_sqldb_api.db.session.add(Job.from_entity(job))
        for job_details in job.details:
            for job_detail in job_details:
                taxii2_sqldb_api.db.session.add(JobDetail.from_entity(job_detail))
    taxii2_sqldb_api.db.session.commit()
    yield jobs


@pytest.fixture(scope="function")
def db_collections(request, taxii2_sqldb_api, db_api_roots):
    try:
        collections = request.param
    except AttributeError:
        collections = COLLECTIONS
    for collection in collections:
        taxii2_sqldb_api.db.session.add(Collection.from_entity(collection))
    taxii2_sqldb_api.db.session.commit()
    yield collections


@pytest.fixture(scope="function")
def db_stix_objects(request, taxii2_sqldb_api, db_collections):
    try:
        stix_objects = request.param
    except AttributeError:
        stix_objects = STIX_OBJECTS
    for stix_object in stix_objects:
        taxii2_sqldb_api.db.session.add(STIXObject.from_entity(stix_object))
    taxii2_sqldb_api.db.session.commit()
    yield stix_objects
