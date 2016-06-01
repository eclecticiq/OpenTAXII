
from .middleware import create_app
from .config import ServerConfig
from .server import TAXIIServer
from .utils import configure_logging

config = ServerConfig()
configure_logging(config.get('logging', {'': 'info'}))

server = TAXIIServer(config)
app = create_app(server)
app.debug = False
