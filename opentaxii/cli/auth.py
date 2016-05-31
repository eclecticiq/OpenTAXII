
import argparse
import structlog

from opentaxii.server import TAXIIServer
from opentaxii.config import ServerConfig
from opentaxii.utils import configure_logging

config = ServerConfig()
configure_logging(config.get('logging'), plain=True)

log = structlog.getLogger(__name__)


def get_parser():
    parser = argparse.ArgumentParser(
        description="Create Account via OpenTAXII Auth API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    return parser


def create_account():

    parser = get_parser()
    parser.add_argument(
        "-u", "--username", dest="username",
        help="Username for the new account", required=True)

    parser.add_argument(
        "-p", "--password", dest="password",
        help="Password for the new account", required=True)

    args = parser.parse_args()

    server = TAXIIServer(config)
    token = server.auth.create_account(args.username, args.password)

    log.info("Account created", username=username, token=token)
