from opentaxii.server import TAXIIServer
from opentaxii.config import ServerConfig
from opentaxii.middleware import create_app
from opentaxii.utils import configure_logging


config = ServerConfig()
configure_logging(config['logging'], plain=True)

server = TAXIIServer(config)

app = create_app(server)
app.debug = True
