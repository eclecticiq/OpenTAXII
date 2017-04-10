import anyconfig
import argparse
import structlog

from opentaxii.taxii.entities import CollectionEntity
from opentaxii.cli import app

log = structlog.getLogger(__name__)


def create_services():

    parser = argparse.ArgumentParser(
        description="Create services using OpenTAXII Persistence API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-c", "--services-config", dest="config",
        help="YAML file with services configuration", required=True)

    args = parser.parse_args()
    services_config = anyconfig.load(args.config, forced_type="yaml")
    services = services_config.get('services', [])

    with app.app_context():

        app.taxii_server.persistence.create_services_from_object(
            services)


def create_collections():

    parser = argparse.ArgumentParser(
        description="Create collections using OpenTAXII Persistence API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-c", "--collections-config", dest="config",
        help="YAML file with collections configuration", required=True)

    args = parser.parse_args()
    collections_config = anyconfig.load(args.config, forced_type="yaml")
    collections = collections_config.get('collections', [])

    with app.app_context():

        created = 0
        for collection in collections:

            service_ids = collection.pop('service_ids')
            existing = None

            for service_id in service_ids:
                existing = app.taxii_server.persistence.get_collection(
                    collection['name'],
                    service_id)
                if existing:
                    break

            if existing:
                log.warning(
                    "collection.skipped.already_exists",
                    collection_name=collection['name'],
                    existing_id=existing.id)
                continue

            c = app.taxii_server.persistence.create_collection(
                CollectionEntity(**collection))

            app.taxii_server.persistence.attach_collection_to_services(
                c.id, service_ids=service_ids)

            created += 1


def delete_content_blocks():

    parser = argparse.ArgumentParser(
        description=(
            "Delete content blocks from specified collections "
            "with timestamp labels matching defined time window"),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-c", "--collection", action="append", dest="collection",
        help="Collection to remove content blocks from", required=True)

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
                collection, start_time=start_time, end_time=end_time)
