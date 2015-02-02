import os
import sys
import logging
import structlog
import urlparse


import intelworks.logging


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



def configure_logging(level, plain_log=False):

    if not plain_log:
        intelworks.logging.configure(level)
    else:
        #renderer = structlog.processors.JSONRenderer() if not plain_log else SimpleRenderer()
        renderer = SimpleRenderer()

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

    logging.getLogger().setLevel(level.upper())
