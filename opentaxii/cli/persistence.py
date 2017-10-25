import anyconfig
import argparse
import structlog

from opentaxii.entities import Account
from opentaxii.cli import app
from opentaxii.local import context
from opentaxii.utils import sync_conf_dict_into_db

log = structlog.getLogger(__name__)

local_admin = Account(
    id=None, username="local-admin", permissions=None, is_admin=True)


def sync_data_configuration():
    parser = argparse.ArgumentParser(
        description="Create services/collections/accounts",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "config", help="YAML file with data configuration")
    parser.add_argument(
        "-f", "--force-delete", dest="force_deletion",
        action="store_true",
        help=("force deletion of collections and their content blocks "
              "if collection is not defined in configuration file"),
        required=False)
    args = parser.parse_args()
    config = anyconfig.load(args.config, forced_type="yaml")

    with app.app_context():
        # run as admin with full access
        context.account = local_admin
        sync_conf_dict_into_db(
            app.taxii_server,
            config,
            force_collection_deletion=args.force_deletion)


def delete_content_blocks():

    parser = argparse.ArgumentParser(
        description=(
            "Delete content blocks from specified collections "
            "with timestamp labels matching defined time window"),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-c", "--collection", action="append", dest="collection",
        help="Collection to remove content blocks from", required=True)
    parser.add_argument(
        "-m", "--with-messages", dest="delete_inbox_messages",
        action="store_true",
        help=("delete inbox messages associated with deleted content blocks"),
        required=False)
    parser.add_argument(
        "--begin", dest="begin",
        help="exclusive beginning of time window as ISO8601 formatted date",
        required=True)
    parser.add_argument(
        "--end", dest="end",
        help="inclusive ending of time window as ISO8601 formatted date")

    args = parser.parse_args()
    with app.app_context():
        start_time = args.begin
        end_time = args.end
        for collection in args.collection:
            app.taxii_server.persistence.delete_content_blocks(
                collection,
                with_messages=args.delete_inbox_messages,
                start_time=start_time,
                end_time=end_time)
