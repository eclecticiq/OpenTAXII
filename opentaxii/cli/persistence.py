import anyconfig
import argparse
import structlog

from opentaxii.config import ServerConfig
from opentaxii.server import TAXIIServer
from opentaxii.utils import configure_logging
from opentaxii.taxii.entities import CollectionEntity

config = ServerConfig()
configure_logging(config.get('logging'), plain=True)

log = structlog.getLogger(__name__)


def get_parser():
    parser = argparse.ArgumentParser(
        description = "Create services via OpenTAXII Auth API",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )
    return parser


def create_services():

    parser = get_parser()

    parser.add_argument("-c", "--services-config", dest="config",
            help="YAML file with services configuration", required=True)

    args = parser.parse_args()

    server = TAXIIServer(config)

    services_config = anyconfig.load(args.config, forced_type="yaml")
    server.persistence.create_services_from_object(services_config)

    log.info("Services created", count=len(services_config))


def create_collections():

    parser = get_parser()

    parser.add_argument("-c", "--collections-config", dest="config",
            help="YAML file with collections configuration", required=True)

    args = parser.parse_args()
    server = TAXIIServer(config)
    collections_config = anyconfig.load(args.config, forced_type="yaml")

    created = 0
    for collection in collections_config:

        service_ids = collection.pop('service_ids')

        existing = None
        # To keep things simple we assume here that collection name
        # is unique globally so we first check if it already exists.
        for service_id in service_ids:
            existing = server.persistence.get_collection(
                collection['name'],
                service_id)
            if existing:
                break

        if existing:
            log.warning("collection.skipped.already_exists",
                     collection_name=collection['name'],
                     existing_id=existing.id)
            continue

        entity = CollectionEntity(**collection)

        c = server.persistence.create_collection(entity)
        server.persistence.attach_collection_to_services(c.id, service_ids=service_ids)
        created += 1

    log.info("Collections created", count=created)
