import os
import sys
import pytz
import logging
import structlog
import urlparse
import importlib

from datetime import datetime
from opentaxii.persistence import DataManager
from opentaxii.taxii.entities import ServiceEntity

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


def create_manager(config):
    api_arguments = config['server']['persistence_api']
    api_class = import_class(api_arguments['class'])
    if api_arguments['parameters']:
        api_instance = api_class(**api_arguments['parameters'])
    else:
        api_instance = api_class()
    return DataManager(api=api_instance)


def create_services_from_config(config, manager=None):

    manager = manager or create_manager(config)

    for _type, id, props in config.services:
        service = manager.create_service(ServiceEntity(id=id, type=_type, properties=props))


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

