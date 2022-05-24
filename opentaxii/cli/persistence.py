import argparse

import structlog
import yaml
from opentaxii.cli import app
from opentaxii.entities import Account
from opentaxii.local import context
from opentaxii.utils import sync_conf_dict_into_db

log = structlog.getLogger(__name__)

local_admin = Account(id=None, username="local-admin", permissions=None, is_admin=True)


def sync_data_configuration():
    parser = argparse.ArgumentParser(
        description="Create services/collections/accounts",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("config", help="YAML file with data configuration")
    parser.add_argument(
        "-f",
        "--force-delete",
        dest="force_deletion",
        action="store_true",
        help=(
            "force deletion of collections and their content blocks "
            "if collection is not defined in configuration file"
        ),
        required=False,
    )
    args = parser.parse_args()
    with open(args.config) as stream:
        config = yaml.safe_load(stream=stream)

    with app.app_context():
        # run as admin with full access
        context.account = local_admin
        sync_conf_dict_into_db(
            app.taxii_server, config, force_collection_deletion=args.force_deletion
        )


def delete_content_blocks():

    parser = argparse.ArgumentParser(
        description=(
            "Delete content blocks from specified collections "
            "with timestamp labels matching defined time window"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--collection",
        action="append",
        dest="collection",
        help="Collection to remove content blocks from",
        required=True,
    )
    parser.add_argument(
        "-m",
        "--with-messages",
        dest="delete_inbox_messages",
        action="store_true",
        help=("delete inbox messages associated with deleted content blocks"),
        required=False,
    )
    parser.add_argument(
        "--begin",
        dest="begin",
        help="exclusive beginning of time window as ISO8601 formatted date",
        required=True,
    )
    parser.add_argument(
        "--end",
        dest="end",
        help="inclusive ending of time window as ISO8601 formatted date",
    )

    args = parser.parse_args()
    with app.app_context():
        start_time = args.begin
        end_time = args.end
        for collection in args.collection:
            app.taxii_server.servers.taxii1.persistence.delete_content_blocks(
                collection,
                with_messages=args.delete_inbox_messages,
                start_time=start_time,
                end_time=end_time,
            )


def add_api_root():
    """CLI command to add taxii2 api root to database."""
    parser = argparse.ArgumentParser(
        description=("Add a new taxii2 ApiRoot object."),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-t", "--title", required=True, help="Title of the api root")
    parser.add_argument(
        "-d", "--description", required=False, help="Description of the api root"
    )
    parser.add_argument(
        "--default", action="store_true", help="Set as default api root"
    )

    args = parser.parse_args()
    with app.app_context():
        app.taxii_server.servers.taxii2.persistence.api.add_api_root(
            title=args.title, description=args.description, default=args.default
        )


def add_collection():
    """CLI command to add taxii2 collection to database."""
    existing_api_root_ids = [
        str(api_root.id)
        for api_root in app.taxii_server.servers.taxii2.persistence.api.get_api_roots()
    ]
    parser = argparse.ArgumentParser(
        description=("Add a new taxii2 Collection object."),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-r",
        "--rootid",
        choices=existing_api_root_ids,
        required=True,
        help="Api root id of the collection",
    )
    parser.add_argument("-t", "--title", required=True, help="Title of the collection")
    parser.add_argument(
        "-d", "--description", required=False, help="Description of the collection"
    )
    parser.add_argument("-a", "--alias", required=False, help="alias of the collection")
    parser.add_argument(
        "--public", action="store_true", help="allow public read access"
    )
    parser.set_defaults(public=False)

    args = parser.parse_args()
    with app.app_context():
        app.taxii_server.servers.taxii2.persistence.api.add_collection(
            api_root_id=args.rootid,
            title=args.title,
            description=args.description,
            alias=args.alias,
            is_public=args.public,
        )


def job_cleanup():
    """CLI command to clean up taxii2 job logs that are >24h old."""
    number_removed = app.taxii_server.servers.taxii2.persistence.api.job_cleanup()
    print(f"{number_removed} removed")
