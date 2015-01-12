import os
import sys
import logging
import importlib
from flask import Flask, request, jsonify

from .options import load_config
from .server import TAXIIServer
from .middleware import TAXIIMiddleware, service_wrapper, attach_error_handlers
from .persistence.sql import SQLDB
from .persistence import DataStorage

config = load_config('default_config.ini', 'TAXII_SERVER_CONFIG')
logging_level = logging.getLevelName(config.logging_level)

app = Flask(__name__)
app.wsgi_app = TAXIIMiddleware(app.wsgi_app)

#app.debug = (logging_level == logging.DEBUG)
#if not app.debug:
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging_level)
app.logger.addHandler(stream_handler)

root_logger = logging.getLogger('taxii_server')
root_logger.addHandler(logging.StreamHandler(sys.stdout))


db = SQLDB(config.db_connection)
db.create_all_tables()

server = TAXIIServer(
    config = config,
    storage = DataStorage(db=db)
)

for path, service in server.path_to_service.items():
    app.add_url_rule(
        path,
        service.uid + "_view",
        view_func = service_wrapper(service),
        methods = ['POST']
    )

attach_error_handlers(app)

for hooks_module in config.storage_hooks:
    importlib.import_module(hooks_module)

