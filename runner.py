from opentaxii.server import create_server
from opentaxii.middleware import create_app
from opentaxii.utils import configure_logging

configure_logging({'' : 'debug'}, plain=True)

server = create_server()

app = create_app(server)
app.debug = True


if __name__ == '__main__':
    app.run(port=9000)

