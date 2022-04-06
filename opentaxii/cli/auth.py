import argparse
import sys

from opentaxii.cli import app


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
        print('token: {}'.format(token))


def is_truely(text):
    if not text:
        return False
    return text[0] == 'y'


def update_account(argv=None):
    parser = argparse.ArgumentParser(
        description="Update Account via OpenTAXII Auth API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    fields = ("password", "admin")
    parser.add_argument("-u", "--username", required=True)
    parser.add_argument("-f", "--field", choices=fields, required=True)
    parser.add_argument("-v", "--value", required=True)

    if argv is None:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)

    with app.app_context():
        accounts = app.taxii_server.auth.get_accounts()
        for account in accounts:
            if account.username != args.username:
                continue
            if args.field == 'password':
                app.taxii_server.auth.update_account(account, password=args.value)
                print('password has been changed')
                return
            if args.field == 'admin':
                account.is_admin = is_truely(args.value)
                account = app.taxii_server.auth.update_account(account, None)
                if account.is_admin:
                    print('now user is admin')
                else:
                    print('now user is mortal')
                return
    print('cannot find account with given username')
