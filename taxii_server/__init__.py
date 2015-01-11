import sys
import os
from flask import Flask, request, jsonify
import importlib

from .options import load_config
from .server import TAXIIServer
from .middleware import TAXIIMiddleware, service_wrapper, attach_error_handlers
from .persistence.sql import SQLDB
from .persistence import DataStorage

app = Flask(__name__)
app.wsgi_app = TAXIIMiddleware(app.wsgi_app)

config = load_config('default_config.ini', 'TAXII_SERVER_CONFIG')

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

