import functools
import importlib
import json

try:
    from re import Pattern
except ImportError:
    from typing.re import Pattern

from typing import Callable, ClassVar, NamedTuple, Optional, Tuple, Type

import structlog
from flask import Flask, Response, request
from werkzeug.exceptions import (Forbidden, MethodNotAllowed, NotAcceptable,
                                 NotFound, RequestEntityTooLarge, Unauthorized,
                                 UnsupportedMediaType)

from opentaxii.persistence.exceptions import (DoesNotExistError,
                                              NoReadNoWritePermission,
                                              NoReadPermission,
                                              NoWritePermission)
from opentaxii.taxii2.utils import taxii2_datetimeformat
from opentaxii.taxii2.validation import (validate_delete_filter_params,
                                         validate_envelope,
                                         validate_list_filter_params,
                                         validate_object_filter_params,
                                         validate_versions_filter_params)
from opentaxii.utils import register_handler

from .auth import AuthManager
from .config import ServerConfig
from .entities import Account
from .exceptions import UnauthorizedException
from .local import context
from .persistence import (BasePersistenceManager, Taxii1PersistenceManager,
                          Taxii2PersistenceManager)
from .taxii2.http import make_taxii2_response
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


class BaseTAXIIServer:
    """
    Base class for common functionality in taxii* servers.
    """

    PERSISTENCE_MANAGER_CLASS: ClassVar[Type[BasePersistenceManager]]
    ENDPOINT_MAPPING: Tuple[(Pattern, Callable[[], Response])]
    app: Flask
    config: dict

    def __init__(self, config: dict):
        self.config = config
        self.persistence = self.PERSISTENCE_MANAGER_CLASS(
            server=self, api=initialize_api(config["persistence_api"])
        )
        self.setup_endpoint_mapping()

    def setup_endpoint_mapping(self):
        mapping = []
        for attr_name in self.__dir__():
            attr = getattr(self, attr_name)
            if hasattr(attr, "registered_url_re"):
                mapping.append((attr.registered_url_re, attr))
        if mapping:
            self.ENDPOINT_MAPPING = tuple(mapping)

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

    def handle_http_exception(self, error):
        return error.get_response()

    def handle_validation_exception(self, error):
        """
        Handle validation exception and return appropriate response.

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

    def check_allowed_methods(self):
        valid_methods = ["POST", "OPTIONS"]
        if request.method not in valid_methods:
            raise MethodNotAllowed(valid_methods=valid_methods)

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
        self.check_allowed_methods()
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

    def handle_http_exception(self, error):
        """Return JSON instead of HTML for HTTP errors."""
        # start with the correct headers and status code from the error
        response = error.get_response()
        # replace the body with JSON
        response.data = json.dumps(
            {
                "code": error.code,
                "name": error.name,
                "description": error.description,
            }
        )
        response.content_type = "application/taxii+json;version=2.1"
        return response

    def handle_validation_exception(self, error):
        """
        Handle validation exception and return appropriate response.
        """
        response = {
            "code": 400,
            "name": "validation error",
            "description": error.messages,
        }
        return make_taxii2_response(response, status=400)

    def get_endpoint(self, relative_path: str) -> Optional[Callable[[], Response]]:
        endpoint = None
        for regex, handler in self.ENDPOINT_MAPPING:
            match = regex.match(relative_path)
            if match:
                endpoint = functools.partial(handler, **match.groupdict())
                break
        if endpoint:
            return functools.partial(self.handle_request, endpoint)

    def check_authentication(self, endpoint: Callable[[], Response]):
        """Check if account is authenticated, unless endpoint handles that itself."""
        if endpoint.func.handles_own_auth:
            # Endpoint will handle auth checks itself
            return
        if context.account is None:
            raise Unauthorized()

    def check_content_length(self):
        if (request.content_length or 0) > self.config["max_content_length"] or len(
            request.data
        ) > self.config[
            "max_content_length"
        ]:  # untestable with flask
            raise RequestEntityTooLarge()

    def check_headers(self, endpoint: Callable[[], Response]):
        if not any(
            [
                valid_accept_mimetype in request.accept_mimetypes
                for valid_accept_mimetype in endpoint.func.registered_valid_accept_mimetypes
            ]
        ):
            raise NotAcceptable()
        if (
            request.method == "POST"
            and request.content_type not in endpoint.func.registered_valid_content_types
        ):
            raise UnsupportedMediaType()

    def check_allowed_methods(self, endpoint: Callable[[], Response]):
        if request.method not in endpoint.func.registered_valid_methods:
            raise MethodNotAllowed(valid_methods=endpoint.func.registered_valid_methods)

    def handle_request(self, endpoint: Callable[[], Response]):
        self.check_authentication(endpoint)
        self.check_content_length()
        self.check_allowed_methods(endpoint)
        self.check_headers(endpoint)
        return endpoint()

    @register_handler(r"^/taxii2/$", handles_own_auth=True)
    def discovery_handler(self):
        if context.account is None and not self.config["public_discovery"]:
            raise Unauthorized()
        response = {
            "title": self.config["title"],
        }
        for key in ["description", "contact"]:
            if self.config.get(key):
                response[key] = self.config.get(key)
        default_api_root, api_roots = self.persistence.get_api_roots()
        if default_api_root:
            response["default"] = f"/taxii2/{default_api_root.id}/"
        response["api_roots"] = [f"/taxii2/{api_root.id}/" for api_root in api_roots]
        return make_taxii2_response(response)

    @register_handler(r"^/taxii2/(?P<api_root_id>[^/]+)/$", handles_own_auth=True)
    def api_root_handler(self, api_root_id):
        try:
            api_root = self.persistence.get_api_root(api_root_id=api_root_id)
        except DoesNotExistError:
            if context.account is None:
                raise Unauthorized()
            raise NotFound()
        if context.account is None and not api_root.is_public:
            raise Unauthorized()
        response = {
            "title": api_root.title,
            "versions": ["application/taxii+json;version=2.1"],
            "max_content_length": self.config["max_content_length"],
        }
        if api_root.description:
            response["description"] = api_root.description
        return make_taxii2_response(response)

    @register_handler(r"^/taxii2/(?P<api_root_id>[^/]+)/status/(?P<job_id>[^/]+)/$")
    def job_handler(self, api_root_id, job_id):
        try:
            job, job_details = self.persistence.get_job_and_details(
                api_root_id=api_root_id, job_id=job_id
            )
        except DoesNotExistError:
            raise NotFound()
        response = {
            "id": job.id,
            "status": job.status,
            "request_timestamp": taxii2_datetimeformat(job.request_timestamp),
            "total_count": job_details.total_count,
            "success_count": len(job_details.success),
            "successes": [
                job_detail.as_taxii2_dict() for job_detail in job_details.success
            ],
            "failure_count": len(job_details.failure),
            "failures": [
                job_detail.as_taxii2_dict() for job_detail in job_details.failure
            ],
            "pending_count": len(job_details.pending),
            "pendings": [
                job_detail.as_taxii2_dict() for job_detail in job_details.pending
            ],
        }
        return make_taxii2_response(response)

    @register_handler(r"^/taxii2/(?P<api_root_id>[^/]+)/collections/$", handles_own_auth=True)
    def collections_handler(self, api_root_id):
        try:
            api_root = self.persistence.get_api_root(api_root_id=api_root_id)
        except DoesNotExistError:
            if context.account is None:
                raise Unauthorized()
            raise NotFound()
        if context.account is None and not api_root.is_public:
            raise Unauthorized()
        collections = self.persistence.get_collections(api_root_id=api_root_id)
        response = {}
        if collections:
            response["collections"] = []
            for collection in collections:
                data = {
                    "id": collection.id,
                    "title": collection.title,
                    "can_read": collection.can_read(context.account),
                    "can_write": collection.can_write(context.account),
                    "media_types": ["application/stix+json;version=2.1"],
                }
                for key in ["description", "alias"]:
                    value = getattr(collection, key, None)
                    if value:
                        data[key] = value
                response["collections"].append(data)
        return make_taxii2_response(response)

    @register_handler(
        r"^/taxii2/(?P<api_root_id>[^/]+)/collections/(?P<collection_id_or_alias>[^/]+)/$",
        handles_own_auth=True,
    )
    def collection_handler(self, api_root_id, collection_id_or_alias):
        try:
            collection = self.persistence.get_collection(
                api_root_id=api_root_id, collection_id_or_alias=collection_id_or_alias
            )
        except DoesNotExistError:
            if context.account is None:
                raise Unauthorized()
            raise NotFound()
        if context.account is None and not collection.can_read(context.account):
            raise Unauthorized()
        response = {
            "id": collection.id,
            "title": collection.title,
            "can_read": collection.can_read(context.account),
            "can_write": collection.can_write(context.account),
            "media_types": ["application/stix+json;version=2.1"],
        }
        for key in ["description", "alias"]:
            value = getattr(collection, key, None)
            if value:
                response[key] = value
        return make_taxii2_response(response)

    @register_handler(
        r"^/taxii2/(?P<api_root_id>[^/]+)/collections/(?P<collection_id_or_alias>[^/]+)/manifest/$",
        handles_own_auth=True,
    )
    def manifest_handler(self, api_root_id, collection_id_or_alias):
        filter_params = validate_list_filter_params(request.args, self.persistence.api)
        try:
            manifest, more = self.persistence.get_manifest(
                api_root_id=api_root_id,
                collection_id_or_alias=collection_id_or_alias,
                **filter_params,
            )
        except (DoesNotExistError, NoReadPermission):
            if context.account is None:
                raise Unauthorized()
            raise NotFound()
        if manifest:
            response = {
                "more": more,
                "objects": [
                    {
                        "id": obj.id,
                        "date_added": taxii2_datetimeformat(obj.date_added),
                        "version": taxii2_datetimeformat(obj.version),
                        "media_type": f"application/stix+json;version={obj.spec_version}",
                    }
                    for obj in manifest
                ],
            }
            headers = {
                "X-TAXII-Date-Added-First": min(
                    obj["date_added"] for obj in response["objects"]
                ),
                "X-TAXII-Date-Added-Last": max(
                    obj["date_added"] for obj in response["objects"]
                ),
            }
        else:
            response = {}
            headers = {}
        return make_taxii2_response(
            response,
            extra_headers=headers,
        )

    @register_handler(
        r"^/taxii2/(?P<api_root_id>[^/]+)/collections/(?P<collection_id_or_alias>[^/]+)/objects/$",
        ("GET", "POST"),
        valid_content_types=("application/taxii+json;version=2.1",),
        handles_own_auth=True,
    )
    def objects_handler(self, api_root_id, collection_id_or_alias):
        if request.method == "GET":
            return self.objects_get_handler(api_root_id, collection_id_or_alias)
        if request.method == "POST":
            return self.objects_post_handler(api_root_id, collection_id_or_alias)

    def objects_get_handler(self, api_root_id, collection_id_or_alias):
        filter_params = validate_list_filter_params(request.args, self.persistence.api)
        try:
            objects, more, next_param = self.persistence.get_objects(
                api_root_id=api_root_id,
                collection_id_or_alias=collection_id_or_alias,
                **filter_params,
            )
        except (DoesNotExistError, NoReadPermission):
            if context.account is None:
                raise Unauthorized()
            raise NotFound()
        if objects:
            response = {
                "more": more,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in objects
                ],
            }
            headers = {
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(
                    min(obj.date_added for obj in objects)
                ),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    max(obj.date_added for obj in objects)
                ),
            }
            if more:
                response["next"] = next_param
        else:
            response = {}
            headers = {}
        return make_taxii2_response(
            response,
            extra_headers=headers,
        )

    def objects_post_handler(self, api_root_id, collection_id_or_alias):
        validate_envelope(request.data)
        try:
            job, job_details = self.persistence.add_objects(
                api_root_id=api_root_id,
                collection_id_or_alias=collection_id_or_alias,
                data=request.get_json(),
            )
        except (DoesNotExistError, NoWritePermission):
            if context.account is None:
                raise Unauthorized()
            raise NotFound()
        response = {
            "id": job.id,
            "status": job.status,
            "request_timestamp": taxii2_datetimeformat(job.request_timestamp),
            "total_count": job_details.total_count,
            "success_count": len(job_details.success),
            "successes": [
                job_detail.as_taxii2_dict() for job_detail in job_details.success
            ],
            "failure_count": len(job_details.failure),
            "failures": [
                job_detail.as_taxii2_dict() for job_detail in job_details.failure
            ],
            "pending_count": len(job_details.pending),
            "pendings": [
                job_detail.as_taxii2_dict() for job_detail in job_details.pending
            ],
        }
        headers = {}
        return make_taxii2_response(
            response,
            202,
            extra_headers=headers,
        )

    @register_handler(
        r"^/taxii2/(?P<api_root_id>[^/]+)/collections/(?P<collection_id_or_alias>[^/]+)/objects/(?P<object_id>[^/]+)/$",
        ("GET", "DELETE"),
        handles_own_auth=True,
    )
    def object_handler(self, api_root_id, collection_id_or_alias, object_id):
        if request.method == "GET":
            return self.object_get_handler(
                api_root_id, collection_id_or_alias, object_id
            )
        if request.method == "DELETE":
            return self.object_delete_handler(
                api_root_id, collection_id_or_alias, object_id
            )

    def object_get_handler(self, api_root_id, collection_id_or_alias, object_id):
        filter_params = validate_object_filter_params(
            request.args, self.persistence.api
        )
        try:
            versions, more, next_param = self.persistence.get_object(
                api_root_id=api_root_id,
                collection_id_or_alias=collection_id_or_alias,
                object_id=object_id,
                **filter_params,
            )
        except (DoesNotExistError, NoReadPermission):
            if context.account is None:
                raise Unauthorized()
            raise NotFound()
        if versions:
            response = {
                "more": more,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in versions
                ],
            }
            headers = {
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(
                    min(obj.date_added for obj in versions)
                ),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    max(obj.date_added for obj in versions)
                ),
            }
            if more:
                response["next"] = next_param
        else:
            response = {}
            headers = {}
        return make_taxii2_response(
            response,
            extra_headers=headers,
        )

    def object_delete_handler(self, api_root_id, collection_id_or_alias, object_id):
        filter_params = validate_delete_filter_params(request.args)
        try:
            self.persistence.delete_object(
                api_root_id=api_root_id,
                collection_id_or_alias=collection_id_or_alias,
                object_id=object_id,
                **filter_params,
            )
        except (DoesNotExistError, NoReadNoWritePermission):
            if context.account is None:
                raise Unauthorized()
            raise NotFound()
        except (NoReadPermission, NoWritePermission):
            if context.account is None:
                raise Unauthorized()
            raise Forbidden()
        return make_taxii2_response("")

    @register_handler(
        (
            r"^/taxii2/(?P<api_root_id>[^/]+)/collections/(?P<collection_id_or_alias>[^/]+)"
            r"/objects/(?P<object_id>[^/]+)/versions/$"
        ),
        handles_own_auth=True,
    )
    def versions_handler(self, api_root_id, collection_id_or_alias, object_id):
        filter_params = validate_versions_filter_params(
            request.args, self.persistence.api
        )
        try:
            versions, more = self.persistence.get_versions(
                api_root_id=api_root_id,
                collection_id_or_alias=collection_id_or_alias,
                object_id=object_id,
                **filter_params,
            )
        except (DoesNotExistError, NoReadPermission):
            if context.account is None:
                raise Unauthorized()
            raise NotFound()
        if versions:
            response = {
                "more": more,
                "versions": [taxii2_datetimeformat(obj.version) for obj in versions],
            }
            headers = {
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(
                    min(obj.date_added for obj in versions)
                ),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    max(obj.date_added for obj in versions)
                ),
            }
        else:
            response = {}
            headers = {}
        return make_taxii2_response(
            response,
            extra_headers=headers,
        )


class ServerMapping(NamedTuple):
    taxii1: Optional[TAXII1Server]
    taxii2: Optional[TAXII2Server]


class TAXIIServer:
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
        servers_kwargs = {
            "taxii1": None,
            "taxii2": None,
        }
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

    @property
    def real_servers(self):
        return [server for server in self.servers if server is not None]

    @property
    def current_server(self):
        try:
            server = context.taxiiserver
        except AttributeError:
            if len(self.real_servers) == 1:
                server = self.real_servers[0]
            else:
                server = None
        return server

    def init_app(self, app: Flask):
        """Connect taxii1, taxii2 and auth to flask."""
        self.app = app
        for server in self.real_servers:
            server.init_app(app)
        self.auth.api.init_app(app)

    def is_basic_auth_supported(self):
        """Check if basic auth is a supported feature."""
        return self.config.get("support_basic_auth", False)

    def get_endpoint(self, relative_path: str) -> Optional[Callable[[], Response]]:
        """Get first endpoint matching relative_path."""
        for server in self.real_servers:
            endpoint = server.get_endpoint(relative_path)
            if endpoint:
                endpoint.server = server
                return endpoint

    def handle_request(self, relative_path: str) -> Response:
        """Dispatch request to appropriate taxii* server."""
        relative_path = "/" + relative_path
        endpoint = self.get_endpoint(relative_path)
        if not endpoint:
            raise NotFound()
        context.taxiiserver = endpoint.server
        return endpoint()

    def handle_internal_error(self, error):
        """Dispatch internal error handling to appropriate taxii* server."""
        return context.taxiiserver.handle_internal_error(error)

    def handle_status_exception(self, error):
        """Dispatch status exception handling to appropriate taxii* server."""
        return context.taxiiserver.handle_status_exception(error)

    def handle_http_exception(self, error):
        """Dispatch http exception handling to appropriate taxii* server."""
        server = self.current_server
        if server:
            return server.handle_http_exception(error)
        else:
            return error.get_response()

    def handle_validation_exception(self, error):
        """Dispatch validation exception handling to appropriate taxii* server."""
        server = self.current_server
        if server:
            return server.handle_validation_exception(error)
        else:
            return error.get_response()

    def raise_unauthorized(self):
        """Dispatch unauthorized handling to appropriate taxii* server."""
        endpoint = self.get_endpoint(request.path)
        if endpoint:
            server = endpoint.server
        else:
            server = self.servers.taxii1
        context.taxiiserver = server
        return server.raise_unauthorized()
