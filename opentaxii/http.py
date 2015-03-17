
from .middleware import create_app
from .config import ServerConfig
from .server import create_server
from .utils import configure_logging

config = ServerConfig()
configure_logging(config.get('logging', {'' : 'info'}))

server = create_server(config)
app = create_app(server)
app.debug = False

