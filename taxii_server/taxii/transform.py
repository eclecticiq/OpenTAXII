
import libtaxii.taxii_default_query as tdq
import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.common import generate_message_id
from libtaxii.constants import *

from lxml.etree import XMLSyntaxError

from .exceptions import StatusMessageException, StatusBadMessage, StatusUnsupportedQuery
from .bindings import MESSAGE_VALIDATOR_PARSER, ContentBinding

import structlog
log = structlog.get_logger(__name__)


def parse_message(content_type, body, do_validate=True):

    validator_parser = MESSAGE_VALIDATOR_PARSER[content_type]

    if do_validate:
        try:
            result = validator_parser.validator.validate_string(body)
            if not result.valid:
                errors = '; '.join([str(err) for err in result.error_log])
                raise StatusBadMessage('Request was not schema valid: %s' % errors)
        except XMLSyntaxError as e:
            log.error("Not well-formed XML. Body: '%s'" % body, exc_info=True)
            raise StatusBadMessage('Request was not well-formed XML', e=e)

    try:
        taxii_message = validator_parser.parser(body)
    except tm11.UnsupportedQueryException as e:
        # TODO: Is it possible to give the real message id?
        # TODO: Is it possible to indicate which query aspects are supported?
        # This might require a change in how libtaxii works
        log.error("Unsupported query", exc_info=True)
        raise StatusUnsupportedQuery()

    return taxii_message




def service_to_instances(service, version):
    service_instances = []

    for binding in service.supported_protocol_bindings:
        
        address = service.absolute_address(binding)

        if version == 10:

            stype = service.service_type
            if stype == SVC_COLLECTION_MANAGEMENT:
                stype = SVC_FEED_MANAGEMENT

            instance = tm10.ServiceInstance(
                service_type = stype,
                services_version = VID_TAXII_SERVICES_10,
                available = service.enabled,
                protocol_binding = binding,
                service_address = address,
                message_bindings = service.supported_message_bindings,
                message = service.description
            )
        elif version == 11:
            instance = tm11.ServiceInstance(
                service_type = service.service_type,
                services_version = VID_TAXII_SERVICES_11,
                available = service.enabled,
                protocol_binding = binding,
                service_address = address,
                message_bindings = service.supported_message_bindings,
                message = service.description
            )
        service_instances.append(instance)

#    if v == 11 and hasattr(service, 'supportd_queries'): for si in service_instances:
#            for sq in service.supported_queries:
#                si.supported_query.append(sq.to_query_info_11())
#    return service_instances

    return service_instances


def to_content_binding(raw_content_binding, version):
    if version == 10:
        return ContentBinding(binding=raw_content_binding, subtypes=None)
    elif version == 11:
        return ContentBinding(binding=raw_content_binding.binding_id,
                subtypes=raw_content_binding.subtype_ids)


def to_content_bindings(bindings, version):
    return map(lambda b: to_content_binding(b, version), bindings)



def get_binding_intersection_10(data_collection, binding_list, in_response_to):
    """
    Given a list of tm10.ContentBinding objects, return the ContentBindingAndSubtypes that are in this
    Data Collection

    :param binding_list: A list of strings representing ContentBinding IDs
    :param in_response_to: The request message's message ID. Used if a StatusMessageException is raised
    :return: A list of ContentBindingAndSubtype objects representing the intersection of this Data Collection's\
             supported Content Bindings and binding_list.
    """

    if binding_list is None or len(binding_list) == 0:
        return None

    matching_cbas = []

    for content_binding in binding_list:
        try:
            cb = ContentBindingAndSubtype.objects.get(content_binding__binding_id=content_binding, subtype=None)  # Subtypes are not in TAXII 1.0
            matching_cbas.append(cb)
        except ContentBindingAndSubtype.DoesNotExist:
            pass # This is OK. Other errors are not

    if len(matching_cbas) == 0:
        if data_collection.accept_all_content:
            bindings = ContentBindingAndSubtype.objects.filter(subtype=None)
        else:
            bindings = data_collection.supported_content.all()

        supported_content = [b.binding_id for b in bindings]
        raise StatusMessageException(in_response_to, ST_UNSUPPORTED_CONTENT_BINDING, status_detail={SD_SUPPORTED_CONTENT: supported_content})

    return matching_cbas

def get_binding_intersection_11(data_collection, binding_list, in_response_to):
    """
    Arguments:
        binding_list - a list of tm11.ContentBinding objects

    Returns:
        A list of ContentBindingAndSubtype objects representing the intersection of this Data Collection's \
        supported Content Bindings and binding_list.

    Raises:
        A StatusMessageException if the intersection is
        an empty set.
    """
    if binding_list is None or len(binding_list) == 0:
        return None

    matching_cbas = []

    for content_binding in binding_list:
        cb_id = content_binding.binding_id
        for subtype_id in content_binding.subtype_ids:
            try:
                cb = ContentBindingAndSubtype.objects.get(content_binding__binding_id=cb_id,
                                                          subtype__subtype_id=subtype_id)
                matching_cbas.append(cb)
            except ContentBindingAndSubtype.DoesNotExist:
                pass  # This is OK. Other errors are not

        if len(content_binding.subtype_ids) == 0:
            matches = ContentBindingAndSubtype.objects.filter(content_binding__binding_id=cb_id)
            matching_cbas.extend(list(matches))

    if len(matching_cbas) == 0:  # No matching ContentBindingAndSubtype objects were found
        if data_collection.accept_all_content:
            bindings = ContentBindingAndSubtype.objects.all()
        else:
            bindings = data_collection.supported_content.all()

        supported_content = [b.to_content_binding_11() for b in bindings]
        raise StatusMessageException(in_response_to, ST_UNSUPPORTED_CONTENT_BINDING, status_detail={SD_SUPPORTED_CONTENT: supported_content})

    return matching_cbas


def to_feed_information_10(data_collection):
    """
    Returns:
        A tm10.FeedInformation object
    """
    fi = tm10.FeedInformation(feed_name=data_collection.name,
                              feed_description=data_collection.description,
                              supported_contents=data_collection.get_supported_content_10() or "TODO: use a different value here",
                              available=data_collection.enabled,
                              push_methods=data_collection.get_push_methods_10(),
                              polling_service_instances=data_collection.get_polling_service_instances_10(),
                              subscription_methods=data_collection.get_subscription_methods_10(),
                              # collection_volume,
                              # collection_type,
                              # and receiving_inbox_services can't be expressed in TAXII 1.0
                              )

    return fi

def to_collection_information_11(data_collection):
    """
    Returns:
        A tm11.CollectionInformation object
        based on this model
    """
    ci = tm11.CollectionInformation(collection_name=data_collection.name,
                                    collection_description=data_collection.description,
                                    supported_contents=data_collection.get_supported_content_11(),
                                    available=data_collection.enabled,
                                    push_methods=data_collection.get_push_methods_11(),
                                    polling_service_instances=data_collection.get_polling_service_instances_11(),
                                    subscription_methods=data_collection.get_subscription_methods_11(),
                                    collection_volume=None,  # TODO: Maybe add this to the model?
                                    collection_type=data_collection.type,
                                    receiving_inbox_services=data_collection.get_receiving_inbox_services_11())
    return ci

def get_supported_content_10(data_collection):
    """
    Returns:
        A list of strings indicating the Content Binding IDs that this
        Data Collection supports. None indicates all are supported.
    """
    return_list = []

    if data_collection.accept_all_content:
        return_list = None  # Indicates accept all
    else:
        for content in data_collection.supported_content.filter(subtype=None):
            return_list.append(content.content_binding.binding_id)
    return return_list

def get_supported_content_11(data_collection):
    """
    Returns:
        A list of tm11.ContentBlock objects indicating which ContentBindings are supported.
        None indicates all are supported.
    """
    return_list = []

    if data_collection.accept_all_content:
        return_list = None  # Indicates accept all
    else:
        supported_content = {}

        for content in data_collection.supported_content.all():
            binding_id = content.content_binding.binding_id
            subtype = content.subtype
            if binding_id not in supported_content:
                supported_content[binding_id] = tm11.ContentBinding(binding_id=binding_id)

            if subtype and subtype.subtype_id not in supported_content[binding_id].subtype_ids:
                supported_content[binding_id].subtype_ids.append(subtype.subtype_id)

        return_list = supported_content.values()

    return return_list


def get_polling_service_instances_10(data_collection):
    """
    Returns a list of tm10.PollingServiceInstance objects
    identifying the TAXII Poll Services that can be polled
    for this Data Collection
    """
    poll_instances = []
    poll_services = PollService.objects.filter(data_collections=data_collection)
    for poll_service in poll_services:
        message_bindings = [mb.binding_id for mb in poll_service.supported_message_bindings.all()]
        for supported_protocol_binding in poll_service.supported_protocol_bindings.all():
            poll_instance = tm10.PollingServiceInstance(supported_protocol_binding.binding_id, poll_service.path, message_bindings)
            poll_instances.append(poll_instance)

    return poll_instances

def get_polling_service_instances_11(data_collection):
    """
    Returns a list of tm11.PollingServiceInstance objects identifying the
    TAXII Poll Services that can be polled for this Data Collection
    """
    poll_instances = []
    poll_services = PollService.objects.filter(data_collections=data_collection)
    for poll_service in poll_services:
        message_bindings = [mb.binding_id for mb in poll_service.supported_message_bindings.all()]
        for supported_protocol_binding in poll_service.supported_protocol_bindings.all():
            poll_instance = tm11.PollingServiceInstance(supported_protocol_binding.binding_id, poll_service.path, message_bindings)
            poll_instances.append(poll_instance)

    return poll_instances

def get_subscription_methods_10(data_collection):
    """
    Returns a list of tm10.SubscriptionMethod objects identifying the TAXII
    Collection Management Services handling subscriptions for this Data Collection
    """
    # TODO: Probably wrong, but here's the idea
    subscription_methods = []
    collection_management_services = CollectionManagementService.objects.filter(advertised_collections=data_collection)
    for collection_management_service in collection_management_services:
        message_bindings = [mb.binding_id for mb in collection_management_service.supported_message_bindings.all()]
        for supported_protocol_binding in collection_management_service.supported_protocol_bindings.all():
            subscription_method = tm10.SubscriptionMethod(supported_protocol_binding.binding_id, collection_management_service.path, message_bindings)
            subscription_methods.append(subscription_method)

    return subscription_methods

def get_subscription_methods_11(data_collection):
    """
    Returns a list of tm11.SubscriptionMethod objects identifying the TAXII
    Collection Management Services handling subscriptions for this Data Collection
    """
    # TODO: Probably wrong, but here's the idea
    subscription_methods = []
    collection_management_services = CollectionManagementService.objects.filter(advertised_collections=data_collection)
    for collection_management_service in collection_management_services:
        message_bindings = [mb.binding_id for mb in collection_management_service.supported_message_bindings.all()]
        for supported_protocol_binding in collection_management_service.supported_protocol_bindings.all():
            subscription_method = tm11.SubscriptionMethod(supported_protocol_binding.binding_id, collection_management_service.path, message_bindings)
            subscription_methods.append(subscription_method)

    return subscription_methods

def get_receiving_inbox_services_11(data_collection):
    """
    Return a set of tm11.ReceivingInboxService objects identifying the TAXII
    Inbox Services that accept content for this Data Collection.
    """
    receiving_inbox_services = []
    inbox_services = InboxService.objects.filter(destination_collections=data_collection)
    for inbox_service in inbox_services:
        message_bindings = [mb.binding_id for mb in inbox_service.supported_message_bindings.all()]
        for supported_protocol_binding in inbox_service.supported_protocol_bindings.all():
            receiving_inbox_service = tm11.ReceivingInboxService(supported_protocol_binding.binding_id,
                                                                 inbox_service.path,
                                                                 message_bindings,
                                                                 # TODO: Work on supported_contents
                                                                 supported_contents=None)

            receiving_inbox_services.append(receiving_inbox_service)

    return receiving_inbox_services


#def clean(self):
#    super(QueryScope, self).clean()
#    try:
#        validation.do_check(self.scope, 'scope', regex_tuple=tdq.targeting_expression_regex)
#    except:
#        raise ValidationError('Scope syntax was not valid. Syntax is a list of: (<item>, *, **, or @<item>) separated by a /. No leading slash.')
#
#    handler_class = self.supported_query.query_handler.get_handler_class()
#
#    # TODO: Do something about this. Make a class?
#    supported, error = handler_class.is_scope_supported(self.scope)
#    if not supported:
#        raise ValidationError('This query scope is not supported by the handler: %s' %
#                              str(error))


def to_feed_information_response_10(collection_management_service, in_response_to):
    """
    Creates a tm10.FeedInformationResponse
    based on this model

    Returns:
        A tm10.FeedInformationResponse object
    """

    # Create a stub FeedInformationResponse
    fir = tm10.FeedInformationResponse(message_id=generate_message_id(), in_response_to=in_response_to)

    # For each collection that is advertised and enabled, create a Feed Information
    # object and add it to the Feed Information Response
    for collection in collection_management_service.advertised_collections.filter(enabled=True):
        fir.feed_informations.append(collection.to_feed_information_10())

    return fir

def to_collection_information_response_11(collection_management_service, in_response_to):
    """
    Creates a tm11.CollectionInformationResponse
    based on this model

    Returns:
        A tm11.CollectionInformationResponse object
    """

    # Create a stub CollectionInformationResponse
    cir = tm11.CollectionInformationResponse(message_id=generate_message_id(), in_response_to=in_response_to)

    # For each collection that is advertised and enabled, create a Collection Information
    # object and add it to the Collection Information Response
    for collection in collection_management_service.advertised_collections.filter(enabled=True):
        cir.collection_informations.append(collection.to_collection_information_11())

    return cir

def validate_collection_name(collection_management_service, collection_name, in_response_to):
    """
    Arguments:
        collection_name (str) - The name of a collection
        in_response_to (str) - The message_id of the request

    Returns:
        A models.DataCollection object, if this CollectionManagementService
        handles subscriptions DataCollection identified by collection_name
        and that DataCollection has enabled=True

    Raises:
        A StatusMessageException if this CollectionManagementService does not
        handle subscriptions for the DataCollection identified by collection_name
        or the DataCollection has enabled=False.
    """
    try:
        data_collection = collection_management_service.advertised_collections.get(collection_name=collection_name, enabled=True)
    except models.DataCollection.DoesNotExist:
        raise StatusMessageException(in_response_to, ST_NOT_FOUND, status_detail={'ITEM': collection_name})

    return data_collection




#######################################################################################################################################



