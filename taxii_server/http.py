
from .middleware import create_app
from .utils import configure_logging

app = create_app()

configure_logging(app.taxii_config.server.logging_level)


