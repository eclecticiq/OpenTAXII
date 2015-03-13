import os
import sys
import pytz
import logging
import structlog
import urlparse
import importlib

from datetime import datetime

from .config import ServerConfig
from .persistence import PersistenceManager
from .taxii.entities import ServiceEntity

def get_path_and_address(domain, address):
    parsed = urlparse.urlparse(address)

    if parsed.scheme:
        return None, address
    else:
        return address, domain + address


class SimpleRenderer(object):

    def __call__(self, logger, name, event_dict):
        if 'exception' in event_dict:
            message = '\n%s' % event_dict['exception']
        else:
            message = event_dict['event']
        return '%(timestamp)s [%(logger)s] %(level)s: %(message)s' % dict(message=message, **event_dict)


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
    return instance


def create_services_from_config(config, persistence_manager):
    for _type, id, props in config.services:
        service = persistence_manager.create_service(ServiceEntity(
            id=id, type=_type, properties=props))


def configure_logging(logging_levels):
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    for logger, level in logging_levels.items():
        logging.getLogger(logger).setLevel(level.upper())


def get_config_for_tests(domain, services, db_connection=None):

    db_connection = db_connection or 'sqlite://' 

    config = ServerConfig()
    config['server']['persistence_api'].update({
        'class' : 'opentaxii.persistence.sqldb.SQLDatabaseAPI',
        'parameters' : {
            'db_connection' : db_connection,
            'create_tables' : True
        }
    })
    config['server']['domain'] = domain
    config['services'].update(services)
    return config


def attach_signal_hooks(config):
    signal_hooks = config['server']['hooks']
    if signal_hooks:
        import_module(signal_hooks)


