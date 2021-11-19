import functools
import importlib
from typing import Callable, ClassVar, NamedTuple, Optional, Type

import structlog
from flask import Flask, Response, abort, request

from .auth import AuthManager
from .config import ServerConfig
from .entities import Account
from .exceptions import UnauthorizedException
from .local import context
from .persistence import (BasePersistenceManager, Taxii1PersistenceManager,
                          Taxii2PersistenceManager)
from .taxii.bindings import (ALL_PROTOCOL_BINDINGS, MESSAGE_BINDINGS,
                             SERVICE_BINDINGS)
from .taxii.exceptions import (FailureStatus, StatusMessageException,
                               raise_failure)
from .taxii.http import (HTTP_ALLOW, HTTP_X_TAXII_CONTENT_TYPES,
                         get_content_type, get_http_headers,
                         make_taxii_response, validate_request_headers,
                         validate_request_headers_post_parse,
                         validate_response_headers)
from .taxii.services import (CollectionManagementService, DiscoveryService,
                             InboxService, PollService)
from .taxii.services.abstract import TAXIIService
from .taxii.status import process_status_exception
from .taxii.utils import configure_libtaxii_xml_parser, parse_message
from .utils import get_path_and_address, initialize_api

log = structlog.get_logger(__name__)

anonymous_full_access = Account(id=None, username=None, permissions={}, is_admin=True)


class BaseTAXIIServer(object):
    """
    Base class for common functionality in taxii* servers.
    """

    PERSISTENCE_MANAGER_CLASS: ClassVar[Type[BasePersistenceManager]]
    app: Flask
    config: dict

    def __init__(self, config: dict):
        self.config = config
        self.persistence = self.PERSISTENCE_MANAGER_CLASS(
            server=self, api=initialize_api(config["persistence_api"])
        )

    def init_app(self, app: Flask):
        """Connect server and persistence to flask."""
        self.app = app
        self.persistence.api.init_app(app)

    def get_domain(self, service_id):
        """Get domain either from request handler or config."""
        dynamic_domain = self.persistence.get_domain(service_id)
        domain = dynamic_domain or self.config.get("domain")
        return domain

    def get_endpoint(self, relative_path: str) -> Optional[Callable[[], Response]]:
        """Get first endpoint matching relative_path."""
        return

    def handle_internal_error(self, error):
        """
        Handle internal error and return appropriate response.

        Placeholder for subclasses to implement.
        """
        return

    def handle_status_exception(self, error):
        """
        Handle status exception and return appropriate response.

        Placeholder for subclasses to implement.
        """
        return

    def raise_unauthorized(self):
        """
        Handle unauthorized access.

        Placeholder for subclasses to implement.
        """
        raise UnauthorizedException()


class TAXII1Server(BaseTAXIIServer):
    """TAXII1 Server class.

    This class keeps Presistence API manager instance for TAXII1
    and creates TAXII1 Service instances on request.

    :param dict config:
        OpenTAXII1 server configuration
    """

    TYPE_TO_SERVICE = {
        "inbox": InboxService,
        "discovery": DiscoveryService,
        "collection_management": CollectionManagementService,
        "poll": PollService,
    }
    PERSISTENCE_MANAGER_CLASS = Taxii1PersistenceManager

    def __init__(self, config: dict):
        super().__init__(config)
        signal_hooks = config["hooks"]
        if signal_hooks:
            importlib.import_module(signal_hooks)
            log.info("signal_hooks.imported", hooks=signal_hooks)

        configure_libtaxii_xml_parser(config["xml_parser_supports_huge_tree"])
        log.info("opentaxii.server_configured")

    def _create_services(self, service_entities):
        """Create :class:`TAXIIService` instances from `service_entities`"""

        discovery_services = []
        services = []

        for entity in service_entities:

            _props = dict(entity.properties)
            _props["server"] = self

            _props["path"], _props["address"] = get_path_and_address(
                self.get_domain(entity.id), _props["address"]
            )

            advertised = _props.pop("advertised_services", None)

            if entity.type not in self.TYPE_TO_SERVICE:
                raise ValueError('Unknown service type "%s"' % entity.type)

            service = self.TYPE_TO_SERVICE[entity.type](id=entity.id, **_props)

            services.append(service)

            if advertised:
                discovery_services.append((service, advertised))

        for service, advertised in discovery_services:
            service.set_advertised_services([s for s in services if s.id in advertised])

        return services

    def get_endpoint(self, relative_path: str) -> Optional[Callable[[], Response]]:
        """Get first endpoint matching relative_path."""
        for endpoint in self.get_services():
            if endpoint.path == relative_path:
                return functools.partial(self.handle_request, endpoint=endpoint)

    def get_services(self, service_ids=None):
        """Get services registered with this TAXII server instance.

        :param list service_ids: list of service IDs (as strings)

        :return: list of services
        :rtype: list of
                :py:class:`opentaxii.taxii.services.abstract.TAXIIService`
        """

        # early return for filtering by empty list of ids
        if service_ids is not None and not service_ids:
            return []

        service_entities = self.persistence.get_services()

        # Services needs to be created all at once to ensure that
        # discovery services list all active advertised services
        services = self._create_services(service_entities)

        if service_ids:
            services = [service for service in services if service.id in service_ids]

        return services

    def get_service(self, id):
        """Get service by ID.

        :param str id: service ID

        :return: service with specified ID or None
        :rtype: :py:class:`opentaxii.taxii.services.abstract.TAXIIService`
        """

        services = self.get_services([id])
        if services:
            return services[0]

    def get_services_for_collection(self, collection, service_type):
        """Get list of services with type ``service_type``, attached
        to collection ``collection``.

        :param `opentaxii.taxii.entities.CollectionEntity` collection:
                    collection in question
        :param str service_type: service type, supported values are
                    listed as keys in :py:attr:`TYPE_TO_SERVICE`

        :return: list of services
        :rtype: list of :py:class:`opentaxii.taxii.services.abstract.TAXIIService`  # noqa
        """

        if service_type not in self.TYPE_TO_SERVICE:
            raise ValueError("Wrong service type: %s" % service_type)

        for_collection = self.persistence.get_services_for_collection(collection)

        ids_for_type = [e.id for e in for_collection if e.type == service_type]

        # Sync services for collection with registered services for this server
        return self.get_services(ids_for_type)

    def handle_request(self, endpoint: TAXIIService):
        """
        Handle request and return appropriate response.

        Process :class:`TAXIIService` with either :meth:`_process_with_service` or :meth:`_process_options_request`.
        """
        if endpoint.authentication_required and context.account is None:
            raise UnauthorizedException(
                status_type=self.config["unauthorized_status"],
            )

        if not endpoint.authentication_required:
            # if endpoint is not protected, full access
            context.account = anonymous_full_access

        if not endpoint.available:
            raise_failure("The service is not available")

        if request.method == "POST":
            return self._process_with_service(endpoint)
        if request.method == "OPTIONS":
            return self._process_options_request(endpoint)

    @staticmethod
    def _process_options_request(service):
        """
        OPTIONS request, return appropriate allow and content types headers.
        """

        message_bindings = ",".join(service.supported_message_bindings or [])

        return (
            "",
            200,
            {HTTP_ALLOW: "POST, OPTIONS", HTTP_X_TAXII_CONTENT_TYPES: message_bindings},
        )

    @classmethod
    def _process_with_service(cls, service) -> Response:
        """
        POST request, return requested data.
        """

        if "application/xml" not in request.accept_mimetypes:
            raise_failure(
                "The specified values of Accept is not supported: {}".format(
                    ", ".join((request.accept_mimetypes or []))
                )
            )

        validate_request_headers(request.headers, MESSAGE_BINDINGS)

        taxii_message = parse_message(get_content_type(request.headers), request.data)

        try:
            validate_request_headers_post_parse(
                request.headers,
                supported_message_bindings=MESSAGE_BINDINGS,
                service_bindings=SERVICE_BINDINGS,
                protocol_bindings=ALL_PROTOCOL_BINDINGS,
            )
        except StatusMessageException as e:
            e.in_response_to = taxii_message.message_id
            raise e

        response_message = service.process(request.headers, taxii_message)

        response_headers = get_http_headers(response_message.version, request.is_secure)
        validate_response_headers(response_headers)

        taxii_xml = response_message.to_xml(pretty_print=True)
        return make_taxii_response(taxii_xml, response_headers)

    def handle_internal_error(self, error):
        """
        Handle internal error and return appropriate response.
        """
        log.error("Internal error", exc_info=True)

        if "application/xml" not in request.accept_mimetypes:
            return "Unacceptable", 406

        if self.config["return_server_error_details"]:
            message = "Server error occurred: {}".format(error)
        else:
            message = "Server error occurred"

        new_error = FailureStatus(message, e=error)
        xml, headers = process_status_exception(
            new_error, request.headers, request.is_secure
        )
        return make_taxii_response(xml, headers)

    def handle_status_exception(self, error):
        """
        Handle status exception and return appropriate response.
        """
        log.warning("Status exception", exc_info=True)

        if "application/xml" not in request.accept_mimetypes:
            return "Unacceptable", 406

        xml, headers = process_status_exception(
            error, request.headers, request.is_secure
        )
        return make_taxii_response(xml, headers)

    def raise_unauthorized(self):
        """
        Handle unauthorized access.
        """
        raise UnauthorizedException(
            status_type=self.config["unauthorized_status"],
        )


class TAXII2Server(BaseTAXIIServer):
    """
    TAXII2 server class.

    Stub, implementation pending.
    """

    PERSISTENCE_MANAGER_CLASS = Taxii2PersistenceManager


class ServerMapping(NamedTuple):
    taxii1: TAXII1Server
    taxii2: TAXII2Server


class TAXIIServer(object):
    """
    TAXII Server class.

    This is the main entrypoint for http requests.
    It keeps the Auth API manager instance and dispatches requests and error handling to
    :class:`TAXII1Server`
    and
    :class:`TAXII2Server`
    """

    AUTH_MANAGER_CLASS: ClassVar[Type[AuthManager]] = AuthManager
    servers: ServerMapping
    app: Flask
    config: ServerConfig

    def __init__(self, config: ServerConfig):
        self.config = config
        servers_kwargs = {}
        if "taxii1" in config and config["taxii1"]:
            servers_kwargs["taxii1"] = TAXII1Server(
                {**config["taxii1"], "domain": config.get("domain")}
            )
        if "taxii2" in config and config["taxii2"]:
            servers_kwargs["taxii2"] = TAXII2Server(
                {**config["taxii2"], "domain": config.get("domain")}
            )
        self.servers = ServerMapping(**servers_kwargs)
        self.auth = self.AUTH_MANAGER_CLASS(
            server=self, api=initialize_api(config["auth_api"])
        )

    def init_app(self, app: Flask):
        """Connect taxii1, taxii2 and auth to flask."""
        self.app = app
        for server in self.servers:
            server.init_app(app)
        self.auth.api.init_app(app)

    def is_basic_auth_supported(self):
        """Check if basic auth is a supported feature."""
        return self.config.get("support_basic_auth", False)

    def get_endpoint(self, relative_path: str) -> Optional[Callable[[], Response]]:
        """Get first endpoint matching relative_path."""
        for server in self.servers:
            endpoint = server.get_endpoint(relative_path)
            if endpoint:
                endpoint.server = server
                return endpoint

    def handle_request(self, relative_path: str) -> Response:
        """Dispatch request to appropriate taxii* server."""
        relative_path = "/" + relative_path
        endpoint = self.get_endpoint(relative_path)
        if not endpoint:
            abort(404)
        context.taxiiserver = endpoint.server
        return endpoint()

    def handle_internal_error(self, error):
        """Dispatch internal error handling to appropriate taxii* server."""
        return context.taxiiserver.handle_internal_error(error)

    def handle_status_exception(self, error):
        """Dispatch status exception handling to appropriate taxii* server."""
        return context.taxiiserver.handle_status_exception(error)

    def raise_unauthorized(self):
        """Dispatch unauthorized handling to appropriate taxii* server."""
        endpoint = self.get_endpoint(request.path)
        if endpoint:
            server = endpoint.server
        else:
            server = self.servers.taxii1
        context.taxiiserver = server
        server.raise_unauthorized()
