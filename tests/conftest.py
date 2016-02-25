
from opentaxii.config import ServerConfig


def get_config_for_tests(domain, persistence_db=None, auth_db=None):

    config = ServerConfig()
    config.update({
        'persistence_api' : {
            'class' : 'opentaxii.persistence.sqldb.SQLDatabaseAPI',
            'parameters' : {
                'db_connection' : persistence_db or 'sqlite://',
                'create_tables' : True
            }
        },
        'auth_api' : {
            'class' : 'opentaxii.auth.sqldb.SQLDatabaseAPI',
            'parameters' : {
                'db_connection' : auth_db or 'sqlite://',
                'create_tables' : True,
                'secret' : 'dummy-secret-string-for-tests'
            }
        }
    })
    config['domain'] = domain
    return config
