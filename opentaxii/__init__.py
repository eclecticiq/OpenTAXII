'''
    OpenTAXII, TAXII server implementation from EclecticIQ.
'''
# flake8: noqa

from ._version import __version__
from .server import TAXIIServer
from .config import ServerConfig
from .entities import Account

from .local import context
