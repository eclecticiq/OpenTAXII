import anyconfig
import argparse
import structlog

from opentaxii.config import ServerConfig
from opentaxii.utils import configure_logging
from opentaxii.server import create_server
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

    server = create_server(config)

    services_config = anyconfig.load(args.config, forced_type="yaml")
    server.persistence.create_services_from_object(services_config)
    server.reload_services()

    log.info("Services created", count=len(services_config))


def create_collections():

    parser = get_parser()

    parser.add_argument("-c", "--collections-config", dest="config",
            help="YAML file with collections configuration", required=True)

    args = parser.parse_args()

    server = create_server(config)

    collections_config = anyconfig.load(args.config, forced_type="yaml")

    for collection in collections_config:

        service_ids = collection.pop('service_ids')

        entity = CollectionEntity(**collection)

        c = server.persistence.create_collection(entity)
        server.persistence.attach_collection_to_services(c.id, services_ids=service_ids)

    log.info("Collections created", count=len(collections_config))
