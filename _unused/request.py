# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import libtaxii as t
import libtaxii.messages_10 as tm10
import libtaxii.messages_11 as tm11
import libtaxii.taxii_default_query as tdq
from libtaxii.constants import *
from functools import wraps

from taxii_services.exceptions import StatusMessageException

# 1. Validate request (headers, POST) [common]
# 2. Deserialize message [pretty common]
# 3. Check message type [common]
# 4. Create response message [uncommon]
# 5. Create response (headers, etc) [common]
# 6. Send to client [common]


class HeaderRule:
    PRESENCE_REQUIRED = 0
    PRESENCE_OPTIONAL = 1
    PRESENCE_PROHIBITED = 2

    def __init__(self, header_name, presence, value_list=None):
        self.header_name = header_name
        self.presence = presence
        self.value_list = value_list or []
        if not isinstance(self.value_list, list):
            self.value_list = [self.value_list]

    @staticmethod
    def evaluate_header_rules(django_request, header_rules):
        """
            django_request - a Django request
            header_rules - A list of HeaderRule objects

            Raises an exception is something is wrong, does nothing if nothing is wrong.
            This is intended to be used by validate_request, but doesn't have to be.
        """
        for rule in header_rules:
            header_name = rule.header_name
            request_value = django_request.META.get(header_name)
            if request_value is None and rule.presence == PRESENCE_REQUIRED:
                raise ValueError('Required header not present: %s' % header_name)
            elif request_value is not None and rule.presence == HeaderRule.PRESENCE_PROHIBITED:
                raise ValueError('Prohibited header is present: %s' % header_name)

            if request_value is None:
                continue

            if request_value not in rule.value_list:
                raise ValueError('Header value not in allowed list. Header name: %s; Allowed values: %s;' % (header_name, rule.value_list))

# Rules you can use for TAXII 1.1 Services
TAXII_11_HeaderRules = [
    HeaderRule('CONTENT_TYPE', HeaderRule.PRESENCE_REQUIRED, 'application/xml'),
    HeaderRule('HTTP_ACCEPT', HeaderRule.PRESENCE_OPTIONAL, 'application/xml'),
    HeaderRule('HTTP_X_TAXII_CONTENT_TYPE', HeaderRule.PRESENCE_REQUIRED, VID_TAXII_XML_11),
    HeaderRule('HTTP_X_TAXII_PROTOCOL', HeaderRule.PRESENCE_REQUIRED, [VID_TAXII_HTTP_10, VID_TAXII_HTTP_10]),
    HeaderRule('HTTP_X_TAXII_ACCEPT', HeaderRule.PRESENCE_OPTIONAL, VID_TAXII_XML_11),
    HeaderRule('HTTP_X_TAXII_SERVICES', HeaderRule.PRESENCE_REQUIRED, VID_TAXII_SERVICES_11)]

# Rules you can use for TAXII 1.0 Services
TAXII_10_HeaderRules = [
    HeaderRule('CONTENT_TYPE', HeaderRule.PRESENCE_REQUIRED, 'application/xml'),
    HeaderRule('HTTP_ACCEPT', HeaderRule.PRESENCE_OPTIONAL, 'application/xml'),
    HeaderRule('HTTP_X_TAXII_CONTENT_TYPE', HeaderRule.PRESENCE_REQUIRED, VID_TAXII_XML_10),
    HeaderRule('HTTP_X_TAXII_PROTOCOL', HeaderRule.PRESENCE_REQUIRED, [VID_TAXII_HTTP_10, VID_TAXII_HTTP_10]),
    HeaderRule('HTTP_X_TAXII_ACCEPT', HeaderRule.PRESENCE_OPTIONAL, VID_TAXII_XML_10),
    HeaderRule('HTTP_X_TAXII_SERVICES', HeaderRule.PRESENCE_REQUIRED, VID_TAXII_SERVICES_10)]

# Rules you can use for TAXII 1.1 & 1.0 services
TAXII_HeaderRules = [
    HeaderRule('CONTENT_TYPE', HeaderRule.PRESENCE_REQUIRED, 'application/xml'),
    HeaderRule('HTTP_ACCEPT', HeaderRule.PRESENCE_OPTIONAL, 'application/xml'),
    HeaderRule('HTTP_X_TAXII_CONTENT_TYPE', HeaderRule.PRESENCE_REQUIRED, [VID_TAXII_XML_10, VID_TAXII_XML_11]),
    HeaderRule('HTTP_X_TAXII_PROTOCOL', HeaderRule.PRESENCE_REQUIRED, [VID_TAXII_HTTP_10, VID_TAXII_HTTP_10]),
    HeaderRule('HTTP_X_TAXII_ACCEPT', HeaderRule.PRESENCE_OPTIONAL, [VID_TAXII_XML_10, VID_TAXII_XML_11]),
    HeaderRule('HTTP_X_TAXII_SERVICES', HeaderRule.PRESENCE_REQUIRED, VID_TAXII_SERVICES_10)]


def validate_taxii(header_rules=TAXII_HeaderRules, message_types=None, do_validate=True):

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            if request.method != 'POST':
                raise StatusMessageException('0', ST_BAD_MESSAGE, 'Request method was not POST!')

            # If requested, attempt to validate
            # TODO: Validation has changed!
            if do_validate:
                try:
                    validate(request)
                except Exception as e:
                    raise StatusMessageException('0', ST_BAD_MESSAGE, e.message)

            # Attempt to deserialize
            try:
                message = deserialize(request)
            except Exception as e:
                raise StatusMessageException('0', ST_BAD_MESSAGE, e.message)

            try:
                if message_types is None:
                    pass  # No checking was requested
                elif isinstance(message_types, list):
                    if message.__class__ not in message_types:
                        raise ValueError('Message type not allowed. Must be one of: %s' % message_types)
                elif isinstance(message_types, object):
                    if not isinstance(message, message_types):
                        raise ValueError('Message type not allowed. Must be: %s' % message_types)
                elif message_types is not None:
                    raise ValueError('Something strange happened with message_types! Was not a list or object!')
            except ValueError as e:
                msg = tm11.StatusMessage(generate_message_id(), message.message_id, status_type='FAILURE', message=e.message)
                return response_utils.HttpResponseTaxii(msg.to_xml(), response_headers)

            kwargs['taxii_message'] = message
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def deserialize(django_request):
    """
    django_request - A django request that contains a TAXII Message to deserialize

    Looks at the TAXII Headers to determine what the TAXII Message _should_ be,
    and looks for a registered deserializer that can deserialize the TAXII Message.

    To register a deserializer, see register_deserializer.
    """
    content_type = django_request.META['CONTENT_TYPE']
    x_taxii_content_type = django_request.META['HTTP_X_TAXII_CONTENT_TYPE']

    deserializer_key = _get_deserializer_key(content_type, x_taxii_content_type)
    deserializer = deserializers.get(deserializer_key)
    if deserializer is None:
        raise Exception('Deserializer not found!')

    return deserializer(django_request.body)


def validate(django_request):
    """
    django_request - A django request that contains a TAXII Message to validate

    Looks at the TAXII Headers to determine what the TAXII Message _should_ be,
    and looks for a registered validator that can validate the TAXII Message.

    To register a validator, see register_deserializer.
    """
    content_type = django_request.META['CONTENT_TYPE']
    x_taxii_content_type = django_request.META['HTTP_X_TAXII_CONTENT_TYPE']

    deserializer_key = _get_deserializer_key(content_type, x_taxii_content_type)
    validator = validators.get(deserializer_key)
    if validator is None:
        raise Exception('Validator not found!')

    return validator(django_request.body)


def _get_deserializer_key(content_type, x_taxii_content_type):
    """
    Internal use only.
    """
    return content_type + x_taxii_content_type

deserializers = {}
validators = {}


def register_deserializer(content_type, x_taxii_content_type, deserialize_function, validate_function=None):
    """
    Registers a deserializer for use.
    content_type - The Content-Type HTTP header value that this deserializer is used for
    x_taxii_content_type - The X-TAXII-Content-Type HTTP header value that this deserializer is used for
    deserialize_function - The deserializer function to be used for the specific content_type and x_taxii_content_type
    validate_function - The validation function to be used for the specific content_type and x_taxii_content_type. Can be None.
                        The validate_function must take a single string argument (representing the request.body) only.
    """
    deserializer_key = _get_deserializer_key(content_type, x_taxii_content_type)
    deserializers[deserializer_key] = deserialize_function
    validators[deserializer_key] = validate_function

# A TAXII XML 1.1 and XML 1.0 Deserializer (libtaxii) is registered by default
register_deserializer('application/xml', VID_TAXII_XML_11, tm11.get_message_from_xml, tm11.validate_xml)
register_deserializer('application/xml', VID_TAXII_XML_10, tm10.get_message_from_xml, tm10.validate_xml)


def deregister_deserializer(content_type, x_taxii_content_type):
    """
    """
    deserializer_key = _get_deserializer_key(content_type, x_taxii_content_type)
    del deserializers[deserializer_key]
