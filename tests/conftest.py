import pytest

from opentaxii.config import ServerConfig
from opentaxii.middleware import create_app
from opentaxii.server import TAXIIServer
from opentaxii.utils import configure_logging
from opentaxii.taxii.converters import dict_to_service_entity
from opentaxii.local import context, release_context

from fixtures import DOMAIN, SERVICES


@pytest.fixture(autouse=True, scope='session')
def setup_logging():
    configure_logging({'': 'debug'})


def prepare_test_config():
    config = ServerConfig()
    config.update({
        'persistence_api': {
            'class': 'opentaxii.persistence.sqldb.SQLDatabaseAPI',
            'parameters': {
                'db_connection': 'sqlite://',
                'create_tables': True}},
        'auth_api': {
            'class': 'opentaxii.auth.sqldb.SQLDatabaseAPI',
            'parameters': {
                'db_connection': 'sqlite://',
                'create_tables': True,
                'secret': 'dummy-secret-string-for-tests'}}})
    config['domain'] = DOMAIN
    return config


@pytest.yield_fixture()
def anonymous_user():
    from opentaxii.middleware import anonymous_full_access
    context.account = anonymous_full_access
    yield
    release_context()


@pytest.fixture
def app():
    context.server = TAXIIServer(prepare_test_config())
    app = create_app(context.server)
    app.config['TESTING'] = True
    return app


@pytest.yield_fixture()
def server(app, anonymous_user):
    yield app.taxii_server
    release_context()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def services(server):
    for service in SERVICES:
        server.persistence.update_service(dict_to_service_entity(service))
