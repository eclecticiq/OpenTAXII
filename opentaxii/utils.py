import sys
import logging
import structlog
import importlib
import base64
import binascii

from six.moves import urllib

from .entities import Account
from .taxii.entities import (
    CollectionEntity, deserialize_content_bindings)
from .taxii.converters import dict_to_service_entity
from .exceptions import InvalidAuthHeader

log = structlog.getLogger(__name__)


def get_path_and_address(domain, address):
    parsed = urllib.parse.urlparse(address)

    if parsed.scheme:
        return None, address
    else:
        return address, domain + address


def import_class(module_class_name):
    module_name, _, class_name = module_class_name.rpartition('.')
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def initialize_api(api_config):
    class_name = api_config['class']
    cls = import_class(class_name)
    params = api_config.get('parameters', None)

    if params:
        instance = cls(**params)
    else:
        instance = cls()

    log.info("api.initialized", api=class_name)

    return instance


def parse_basic_auth_token(token):
    print("'{}'".format(token), len(token))
    try:
        value = base64.b64decode(token)
    except (TypeError, binascii.Error):
        raise InvalidAuthHeader("Can't decode Basic Auth header value")

    try:
        value = value.decode('utf-8')
        username, password = value.split(':', 1)
        return (username, password)
    except ValueError:
        raise InvalidAuthHeader("Invalid Basic Auth header value")


class PlainRenderer(object):

    def __call__(self, logger, name, event_dict):
        details = event_dict.copy()
        timestamp = details.pop('timestamp')
        logger = details.pop('logger')
        level = details.pop('level')
        event = details.pop('event')
        pairs = ', '.join(['%s=%s' % (k, v) for k, v in details.items()])
        return (
            '{timestamp} [{logger}] {level}: {event} {pairs}'
            .format(
                timestamp=timestamp,
                logger=logger,
                level=level,
                event=event,
                pairs=('{{{}}}'.format(pairs) if pairs else "")))


def configure_logging(logging_levels, plain=False, stream=sys.stderr):
    renderer = (
        PlainRenderer() if plain else
        structlog.processors.JSONRenderer())

    attr_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt='iso')
    ]

    structlog.configure_once(
        processors=(
            [structlog.stdlib.filter_by_level] +
            attr_processors +
            [
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter
            ]
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer, foreign_pre_chain=attr_processors)

    handler = AtomicStreamHandler(stream)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]

    # warnings issued by the ``warnings`` module will be
    # redirected to the ``py.warnings`` logger
    logging.captureWarnings(True)

    for logger, level in logging_levels.items():

        if logger.lower() == 'root':
            logger = ''

        logging.getLogger(logger).setLevel(level.upper())


class AtomicStreamHandler(logging.StreamHandler):
    """A ``StreamHandler`` override that provides ``emit`` method which
    does only one ``write`` per record to the underlying stream. This
    is to keep an individual logging record per line. It's important
    for JSON logging.

    In our case we have pre-forked gunicorn worker processes which
    inherit ``stdout`` from the master process and write into it
    concurrently [1]_. Kernel has the following guarantee for
    write [2]_::

        The adjustment of the file offset and the write operation
        are performed as an atomic step.

    On Python side, ``_io.TextIOWrapper``, which is the type of
    ``sys.stdout``, doesn't provide explicit guarantee but experiments
    show that for records of 8KB and 50 forked processes, lines are
    not interleaved.

    Output stream buffering [3]_ doesn't seem to have an effect.

    .. [1]: https://github.com/benoitc/gunicorn/issues/1272
    .. [2]: https://linux.die.net/man/2/write
    .. [3]: https://eklitzke.org/stdout-buffering
    """

    def emit(self, record):
        try:
            msg = self.format(record)
            self.stream.write('%s\n' % msg)
            self.flush()
        except Exception:
            self.handleError(record)


def sync_conf_dict_into_db(server, config, force_collection_deletion=False):
    services = config.get('services', [])
    sync_services(server, services)
    collections = config.get('collections', [])
    sync_collections(
        server, collections, force_deletion=force_collection_deletion)
    accounts = config.get('accounts', [])
    sync_accounts(server, accounts)


def sync_services(server, services):
    manager = server.persistence

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


def sync_collections(server, collections, force_deletion=False):
    manager = server.persistence

    defined_by_name = {c['name']: c for c in collections}
    existing_by_name = {c.name: c for c in manager.get_collections()}

    created_counter = 0
    updated_counter = 0

    for collection in collections:
        existing = existing_by_name.get(collection['name'])
        collection_data = collection.copy()
        service_ids = collection_data.pop('service_ids')
        if existing:
            collection_data.pop('id', None)
            bindings = deserialize_content_bindings(
                collection_data.pop('supported_content', []))
            for k, v in collection_data.items():
                setattr(existing, k, v)
            existing.supported_content = bindings
            cobj = manager.update_collection(existing)
            manager.set_collection_services(cobj.id, service_ids)
            log.info(
                "sync_collections.updated", name=cobj.name, id=cobj.id)
            updated_counter += 1
        else:
            cobj = manager.create_collection(
                CollectionEntity(**collection_data))
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


def sync_accounts(server, accounts):
    manager = server.auth

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
