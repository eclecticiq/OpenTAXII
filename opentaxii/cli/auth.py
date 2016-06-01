
import argparse
import structlog

from opentaxii.cli import app

log = structlog.getLogger(__name__)


def create_account():

    parser = argparse.ArgumentParser(
        description="Create Account via OpenTAXII Auth API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-u", "--username", dest="username",
        help="Username for the new account", required=True)

    parser.add_argument(
        "-p", "--password", dest="password",
        help="Password for the new account", required=True)

    args = parser.parse_args()

    with app.app_context():

        account = app.taxii_server.auth.create_account(
            args.username, args.password)

        token = app.taxii_server.auth.authenticate(
            account.username, args.password)

        log.info("account.token", token=token, username=account.username)
