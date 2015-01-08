import os
_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True

INBOX_QUEUE = 'queue:inbox'

DOMAIN_NAME = 'dev.intelworks.com'

DB_CONNECTION_STRING = "sqlite:///" + os.path.join(_basedir, "server.db")
