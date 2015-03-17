import structlog

from .config import ServerConfig
from .utils import configure_logging

config = ServerConfig()
configure_logging(config.get('logging'), plain=True)

log = structlog.getLogger(__name__)

