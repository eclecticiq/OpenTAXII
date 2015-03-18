
from opentaxii.server import create_server
from opentaxii.middleware import create_app
from opentaxii.utils import configure_logging
from opentaxii.config import ServerConfig


def run_in_dev_mode():

    config = ServerConfig()
    configure_logging(config['logging'], plain=True)

    server = create_server(config)

    app = create_app(server)
    app.debug = True

    app.run(port=9000)
