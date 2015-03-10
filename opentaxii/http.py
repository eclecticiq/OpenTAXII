
from .middleware import create_app
from .config import ServerConfig
from .utils import configure_logging

config = ServerConfig()
app = create_app(config)

configure_logging(config.get('logging', {'' : 'info'}))
