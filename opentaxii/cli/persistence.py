import anyconfig
import argparse
import structlog

from opentaxii.taxii.entities import (
    CollectionEntity, deserialize_content_bindings)
from opentaxii.entities import Account
from opentaxii.cli import app
from opentaxii.taxii.converters import dict_to_service_entity

log = structlog.getLogger(__name__)


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

    services = config.get('services', [])
    collections = config.get('collections', [])
    accounts = config.get('accounts', [])

    with app.app_context():
        sync_services(services)
        sync_collections(collections, force_deletion=args.force_deletion)
        sync_accounts(accounts)


def sync_services(services):
    manager = app.taxii_server.persistence

    defined_by_id = {s['id']: s for s in services}
    existing_by_id = {s.id: s for s in manager.get_services()}

    created_counter = 0
    updated_counter = 0

    for service in services:
        existing = existing_by_id.get(service['id'])
        if existing:
            properties = service.copy()
            properties.pop('id')
            existing.type = properties.pop('type')
            existing.properties = properties
            existing = manager.update_service(existing)
            log.info("sync_services.updated", id=existing.id)
            updated_counter += 1
        else:
            service = dict_to_service_entity(service)
            sobj = manager.create_service(service)
            log.info("sync_services.created", id=sobj.id)
            created_counter += 1

    deleted_counter = 0
    missing_ids = set(existing_by_id.keys()) - set(defined_by_id.keys())
    for missing_id in missing_ids:
        manager.delete_service(missing_id)
        deleted_counter += 1
        log.info("sync_services.deleted", id=missing_id)

    log.info(
        "sync_services.stats",
        updated=updated_counter,
        created=created_counter,
        deleted=deleted_counter)


def sync_collections(collections, force_deletion=False):
    manager = app.taxii_server.persistence

    defined_by_name = {c['name']: c for c in collections}
    existing_by_name = {c.name: c for c in manager.get_collections()}

    created_counter = 0
    updated_counter = 0

    for collection in collections:
        existing = existing_by_name.get(collection['name'])
        service_ids = collection.pop('service_ids')
        if existing:
            collection.pop('id', None)
            bindings = deserialize_content_bindings(
                collection.pop('supported_content', []))
            for k, v in collection.items():
                setattr(existing, k, v)
            existing.supported_content = bindings
            cobj = manager.update_collection(existing)
            manager.set_collection_services(cobj.id, service_ids)
            log.info(
                "sync_collections.updated", name=cobj.name, id=cobj.id)
            updated_counter += 1
        else:
            cobj = manager.create_collection(CollectionEntity(**collection))
            manager.set_collection_services(cobj.id, service_ids)
            log.info(
                "sync_collections.created", name=cobj.name, id=cobj.id)
            created_counter += 1

    disabled_counter = 0
    deleted_counter = 0
    missing_names = set(existing_by_name.keys()) - set(defined_by_name.keys())
    for name in missing_names:
        if force_deletion:
            manager.delete_collection(name)
            deleted_counter += 1
            log.info("sync_collections.deleted", name=name)
        else:
            collection = existing_by_name[name]
            collection.available = False
            manager.update_collection(cobj)
            disabled_counter += 1
            log.info("sync_collections.disabled", name=name)
    log.info(
        "sync_collections.stats",
        updated=updated_counter,
        created=created_counter,
        disabled=disabled_counter,
        deleted=deleted_counter)


def sync_accounts(accounts):
    manager = app.taxii_server.auth

    defined_by_username = {a['username']: a for a in accounts}
    existing_by_username = {a.username: a for a in manager.get_accounts()}

    created_counter = 0
    updated_counter = 0
    for account in accounts:
        existing = existing_by_username.get(account['username'])
        if existing:
            properties = account.copy()
            password = properties.pop('password')
            existing.permissions = properties.get('permissions', {})
            existing.is_admin = properties.get('is_admin', False)
            existing = manager.update_account(existing, password)
            log.info("sync_accounts.updated", username=existing.username)
            updated_counter += 1
        else:
            obj = Account(
                id=None,
                username=account['username'],
                permissions=account.get('permissions', {}),
                is_admin=account.get('is_admin', False))
            obj = manager.update_account(obj, account['password'])
            log.info("sync_accounts.created", username=obj.username)
            created_counter += 1
    deleted_counter = 0
    missing_usernames = (
        set(existing_by_username.keys()) - set(defined_by_username.keys()))
    for username in missing_usernames:
        manager.delete_account(username)
        deleted_counter += 1
        log.info("sync_accounts.deleted", username=username)

    log.info(
        "sync_accounts.stats",
        updated=updated_counter,
        created=created_counter,
        deleted=deleted_counter)


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
