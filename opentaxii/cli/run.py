
from opentaxii.server import create_server
from opentaxii.middleware import create_app
from opentaxii.utils import configure_logging

configure_logging({'' : 'debug'}, plain=True)

def run_in_dev_mode():

    server = create_server()

    app = create_app(server)
    app.debug = True

    app.run(port=9000)
