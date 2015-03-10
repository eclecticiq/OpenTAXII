from opentaxii.config import ServerConfig
from opentaxii.middleware import create_app
from opentaxii.utils import configure_logging

config = ServerConfig()
app = create_app(config)
configure_logging({'' : 'debug'})

if __name__ == '__main__':
    app.run(port=9000)

