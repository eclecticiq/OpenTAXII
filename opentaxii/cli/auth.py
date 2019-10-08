import sys

import argparse
import structlog

from opentaxii.cli import app


log = structlog.getLogger(__name__)


def create_account(argv=None):

    parser = argparse.ArgumentParser(
        description="Create Account via OpenTAXII Auth API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("-u", "--username", required=True)
    parser.add_argument("-p", "--password", required=True)
    parser.add_argument("-a", "--admin", action="store_true", help="grant admin access")

    if argv is None:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)

    with app.app_context():
        account = app.taxii_server.auth.api.create_account(
            username=args.username,
            password=args.password,
        )
        token = app.taxii_server.auth.authenticate(
            username=account.username,
            password=args.password,
        )
        log.info("account.token", token=token, username=account.username)
