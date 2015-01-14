import os
import sys
import logging.config
import importlib
from flask import Flask, request, jsonify

from .options import load_config
config = load_config()

from .server import TAXIIServer
from .persistence.sql import SQLDB
from .persistence import DataStorage
from .taxii.exceptions import StatusMessageException
from . import middleware

app = Flask(__name__)

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
        view_func = middleware.service_wrapper(service),
        methods = ['POST']
    )

@app.errorhandler(500)
def handle_error(error):
    return middleware.handle_internal_error(error)


@app.errorhandler(StatusMessageException)
def handle_exc(error):
    return middleware.handle_status_exception(error)


for hooks_module in config.storage_hooks:
    importlib.import_module(hooks_module)

