import sys
import logging
import structlog
import urlparse
import importlib

from .config import ServerConfig
from .taxii.entities import ServiceEntity
from .taxii.http import HTTP_AUTHORIZATION

AUTH_HEADER_TOKEN_PREFIX = 'Bearer'.lower()

log = structlog.getLogger(__name__)


def get_path_and_address(domain, address):
    parsed = urlparse.urlparse(address)

    if parsed.scheme:
        return None, address
    else:
        return address, domain + address


def import_class(module_class_name):
    module_name, _, class_name = module_class_name.rpartition('.')
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def import_module(module_name):
    importlib.import_module(module_name)


def load_api(api_config):
    cls = import_class(api_config['class'])
    params = api_config['parameters']

    if params:
        instance = cls(**params)
    else:
        instance = cls()
    log.debug("API loaded", api_class=api_config['class'])
    return instance


def extract_token(headers):
    header = headers.get(HTTP_AUTHORIZATION)
    if not header:
        return

    parts = header.split()

    if parts[0].lower() != AUTH_HEADER_TOKEN_PREFIX or len(parts) == 1 \
            or len(parts) > 2:
        return

    return parts[1]


class PlainRenderer(object):

    def __call__(self, logger, name, event_dict):
        pairs = ', '.join(['%s=%s' % (k, v) for k, v in event_dict.items()])
        return '%(timestamp)s [%(logger)s] %(level)s: %(event)s {%(pairs)s}' \
                % dict(pairs=pairs, **event_dict)


def configure_logging(logging_levels, plain=False):

    _remove_all_existing_log_handlers()

    renderer = PlainRenderer() if plain \
            else structlog.processors.JSONRenderer()

    structlog.configure(
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer
        ],
        context_class = dict,
        logger_factory = structlog.stdlib.LoggerFactory(),
        wrapper_class = structlog.stdlib.BoundLogger,
        cache_logger_on_first_use = True,
    )

    handler = logging.StreamHandler(sys.stdout)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    for logger, level in logging_levels.items():
        logging.getLogger(logger).setLevel(level.upper())


def _remove_all_existing_log_handlers():
    for logger in logging.Logger.manager.loggerDict.values():
        if hasattr(logger, 'handlers'):
            del logger.handlers[:]

    root_logger = logging.getLogger()
    del root_logger.handlers[:]


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


def attach_signal_hooks(config):
    signal_hooks = config['hooks']
    if signal_hooks:
        import_module(signal_hooks)


