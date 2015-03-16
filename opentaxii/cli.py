import argparse
import structlog

from .config import ServerConfig
from .server import create_server
from .utils import configure_logging

log = structlog.getLogger('opentaxii.cli')


def get_parser():
    parser = argparse.ArgumentParser(
        description = "OpenTAXII CLI tools",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )
    return parser


def create_account():

    parser = get_parser()
    parser.add_argument("-u", "--username", help="Username for the new account", required=True)
    parser.add_argument("-p", "--password", help="Password for the new account", required=True)

    parser.parse_args()

    config = ServerConfig()
    configure_logging(config)
    server = create_server(config)

    token = server.auth.create_account(args.username, args.password)

    log.info("Account created", token=token)



if __name__ == '__main__':
    create_account()
