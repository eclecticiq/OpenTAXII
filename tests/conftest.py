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


def get_config_for_tests(domain=DOMAIN, persistence_db=None, auth_db=None):

    config = ServerConfig()
    config.update({
        'persistence_api': {
            'class': 'opentaxii.persistence.sqldb.SQLDatabaseAPI',
            'parameters': {
                'db_connection': persistence_db or 'sqlite://',
                'create_tables': True
            }
        },
        'auth_api': {
            'class': 'opentaxii.auth.sqldb.SQLDatabaseAPI',
            'parameters': {
                'db_connection': auth_db or 'sqlite://',
                'create_tables': True,
                'secret': 'dummy-secret-string-for-tests'
            }
        }
    })
    config['domain'] = domain
    return config


@pytest.fixture()
def config(request):
    return get_config_for_tests()


@pytest.yield_fixture()
def anonymous_user():
    from opentaxii.middleware import anonymous
    context.account = anonymous
    yield
    release_context()


@pytest.fixture()
def server(config, anonymous_user):
    context.server = TAXIIServer(config)
    yield context.server
    release_context()


@pytest.fixture()
def client(server):
    app = create_app(server)
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture()
def services(server):
    for service in SERVICES:
        server.persistence.update_service(dict_to_service_entity(service))
