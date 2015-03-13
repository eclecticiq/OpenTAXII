
from .middleware import create_app
from .server import create_server
from .utils import configure_logging

server = create_server()
app = create_app(server)

configure_logging(app.taxii.config.get('logging', {'' : 'info'}))
