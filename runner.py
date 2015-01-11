
import logging
from colorlog import ColoredFormatter

rootLog = logging.getLogger('')
log = logging.getLogger(__name__)

formatter = ColoredFormatter(
    "%(asctime)s %(name)s %(log_color)s%(levelname)s:%(reset)s %(white)s%(message)s",
    datefmt = None,
    reset = True,
    log_colors = {
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red',
    }
)

handlers = logging.StreamHandler()
handlers.setFormatter(formatter)
log.addHandler(handlers)
rootLog.addHandler(handlers)

rootLog.setLevel(logging.DEBUG)

from taxii_server import app

def run_server():
    app.debug = True
    app.run(port=9000)


if __name__ == '__main__':
    run_server()
