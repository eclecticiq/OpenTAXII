
from .middleware import create_app
from .config import ServerConfig
from .server import TAXIIServer
from .utils import configure_logging


# This module is also used as a Gunicorn configuration module, i.e. passed
# as ``--config python:opentaxii.http``. ``logconfig_dict`` module-level
# variable is recognised by Gunicorn >= 19.8.  The desired effect is to
# remove ``gunicorn.error`` logger's stream handler and restore
# propagation to the root logger, which should follow our
# ``structlog`` configuration.
logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'gunicorn.error': {
            'level': 'INFO',
            'propagate': True
        }
    }
}

config_obj = ServerConfig()
configure_logging(config_obj.get('logging', {'': 'info'}))

server = TAXIIServer(config_obj)
app = create_app(server)
app.debug = False
