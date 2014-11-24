# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import datetime
import sys
import models
from .exceptions import StatusMessageException

import libtaxii.taxii_default_query as tdq
from libtaxii.constants import *

from copy import deepcopy
from dateutil.tz import tzutc
from importlib import import_module

# TODO: Do these headers belong somewhere else?

#: Django version of Content Type
DJANGO_CONTENT_TYPE = 'CONTENT_TYPE'
#: Django version of Accept
DJANGO_ACCEPT = 'HTTP_ACCEPT'
#: Django version of X-TAXII-Content-Type
DJANGO_X_TAXII_CONTENT_TYPE = 'HTTP_X_TAXII_CONTENT_TYPE'
#: Django version of X-TAXII-Protocol
DJANGO_X_TAXII_PROTOCOL = 'HTTP_X_TAXII_PROTOCOL'
#: Django version of X-TAXII-Accept
DJANGO_X_TAXII_ACCEPT = 'HTTP_X_TAXII_ACCEPT'
#: Django version of X-TAXII-Services
DJANGO_X_TAXII_SERVICES = 'HTTP_X_TAXII_SERVICES'

# TODO: Maybe these header values belong in libtaxii.constants?

#: HTTP Content Type header. Used in response message.
HTTP_CONTENT_TYPE = 'Content-Type'
#: HTTP  header. Used in response message.
HTTP_ACCEPT = 'Accept'
#: HTTP X-TAXII-Content-Type header. Used in response message.
HTTP_X_TAXII_CONTENT_TYPE = 'X-TAXII-Content-Type'
#: HTTP X-TAXII-Protocol header. Used in response message.
HTTP_X_TAXII_PROTOCOL = 'X-TAXII-Protocol'
#: HTTP X-TAXII-Accept header. Used in response message.
HTTP_X_TAXII_ACCEPT = 'X-TAXII-Accept'
#: HTTP X-TAXII-Services header. Used in response message.
HTTP_X_TAXII_SERVICES = 'X-TAXII-Services'

REQUIRED_RESPONSE_HEADERS = (HTTP_CONTENT_TYPE, HTTP_X_TAXII_CONTENT_TYPE, HTTP_X_TAXII_PROTOCOL, HTTP_X_TAXII_SERVICES)


def get_service_from_path(path):
    """
    Given a path, return a TAXII Service model object.
    If no service is found, raise Http404.
    """
    # Note that because these objects all inherit from models._TaxiService,
    # which defines the path field, paths are guaranteed to be unique.
    # That said, this can probably be done more efficiently
    print path
    try:
        return models.InboxService.objects.get(path=path, enabled=True)
    except:
        pass

    try:
        return models.DiscoveryService.objects.get(path=path, enabled=True)
    except:
        pass

    try:
        return models.PollService.objects.get(path=path, enabled=True)
    except:
        pass

    try:
        return models.CollectionManagementService.objects.get(path=path, enabled=True)
    except:
        pass

    raise Http404("No TAXII service at specified path")


def get_message_handler(service, taxii_message):
    """
    Given a service and a TAXII Message, return the
    message handler class.
    """

    # Convenience aliases
    st = service.service_type
    mt = taxii_message.message_type

    handler = None
    try:
        if st == SVC_INBOX and mt == MSG_INBOX_MESSAGE:
            handler = service.inbox_message_handler
        elif st == SVC_POLL and mt == MSG_POLL_REQUEST:
            handler = service.poll_request_handler
        elif st == SVC_POLL and mt == MSG_POLL_FULFILLMENT_REQUEST:
            handler = service.poll_fulfillment_handler
        elif st == SVC_DISCOVERY and mt == MSG_DISCOVERY_REQUEST:
            handler = service.discovery_handler
        elif st == SVC_COLLECTION_MANAGEMENT and mt in (MSG_COLLECTION_INFORMATION_REQUEST, MSG_FEED_INFORMATION_REQUEST):
            handler = service.collection_information_handler
        elif st == SVC_COLLECTION_MANAGEMENT and mt in (MSG_MANAGE_COLLECTION_SUBSCRIPTION_REQUEST, MSG_MANAGE_FEED_SUBSCRIPTION_REQUEST):
            handler = service.subscription_management_handler
    except models.MessageHandler.DoesNotExist:
        raise StatusMessageException(taxii_message.message_id, ST_FAILURE, "The MessageHandler lookup failed for service at %s" % service.path)

    if not handler:
        raise StatusMessageException(taxii_message.message_id, ST_FAILURE, "Message Type: %s is not supported by %s" % (mt, st))

    module_name, class_name = handler.handler.rsplit('.', 1)

    try:
        module = import_module(module_name)
        handler_class = getattr(module, class_name)
    except Exception as e:
        type_, value, traceback = sys.exc_info()
        raise type_, ("Error importing handler: %s" % handler.handler, type, value), traceback

    return handler_class


#class HttpResponseTaxii(HttpResponse):
#    """
#    A Django TAXII HTTP Response. Extends the base django.http.HttpResponse
#    to allow quick and easy specification of TAXII HTTP headers.in
#    """
#    def __init__(self, taxii_xml, taxii_headers, *args, **kwargs):
#        super(HttpResponse, self).__init__(*args, **kwargs)
#        self.content = taxii_xml
#        for h in REQUIRED_RESPONSE_HEADERS:
#            if h not in taxii_headers:
#                raise ValueError("Required response header not specified: %s" % h)
#
#        for k, v in taxii_headers.iteritems():
#            self[k.lower()] = v

TAXII_11_HTTPS_Headers = {HTTP_CONTENT_TYPE: 'application/xml',
                          HTTP_X_TAXII_CONTENT_TYPE: VID_TAXII_XML_11,
                          HTTP_X_TAXII_PROTOCOL: VID_TAXII_HTTPS_10,
                          HTTP_X_TAXII_SERVICES: VID_TAXII_SERVICES_11}

TAXII_11_HTTP_Headers = {HTTP_CONTENT_TYPE: 'application/xml',
                         HTTP_X_TAXII_CONTENT_TYPE: VID_TAXII_XML_11,
                         HTTP_X_TAXII_PROTOCOL: VID_TAXII_HTTP_10,
                         HTTP_X_TAXII_SERVICES: VID_TAXII_SERVICES_11}

TAXII_10_HTTPS_Headers = {HTTP_CONTENT_TYPE: 'application/xml',
                          HTTP_X_TAXII_CONTENT_TYPE: VID_TAXII_XML_10,
                          HTTP_X_TAXII_PROTOCOL: VID_TAXII_HTTPS_10,
                          HTTP_X_TAXII_SERVICES: VID_TAXII_SERVICES_10}

TAXII_10_HTTP_Headers = {HTTP_CONTENT_TYPE: 'application/xml',
                         HTTP_X_TAXII_CONTENT_TYPE: VID_TAXII_XML_10,
                         HTTP_X_TAXII_PROTOCOL: VID_TAXII_HTTP_10,
                         HTTP_X_TAXII_SERVICES: VID_TAXII_SERVICES_10}


def get_headers(taxii_services_version, is_secure):
    """
    Convenience method for selecting headers
    """
    if taxii_services_version == VID_TAXII_SERVICES_11 and is_secure:
        return deepcopy(TAXII_11_HTTPS_Headers)
    elif taxii_services_version == VID_TAXII_SERVICES_11 and not is_secure:
        return deepcopy(TAXII_11_HTTP_Headers)
    elif taxii_services_version == VID_TAXII_SERVICES_10 and is_secure:
        return deepcopy(TAXII_10_HTTPS_Headers)
    elif taxii_services_version == VID_TAXII_SERVICES_10 and not is_secure:
        return deepcopy(TAXII_10_HTTP_Headers)
    else:
        raise ValueError("Unknown combination for taxii_services_version and is_secure!")


def create_result_set(poll_service, prp, results):
    """
    Creates a result set and result set parts depending on parameters
    """

    # Create the parent result set
    result_set = models.ResultSet()
    result_set.data_collection = prp.collection
    result_set.total_content_blocks = len(results)
    result_set.last_part_returned = None
    result_set.expires = datetime.datetime.now(tzutc()) + datetime.timedelta(days=7)  # Result Sets expire after a week
    # TODO: Make some part of the database that actually clears out old ResultSets
    result_set.save()

    # Create the individual parts
    content_blocks_per_result_set = poll_service.max_result_size
    part_number = 1
    i = 0
    while i < len(results):
        rsp = models.ResultSetPart()
        rsp.result_set = result_set
        rsp.part_number = part_number

        # Pick out the content blocks that will be part of this result set
        content_blocks = results[i: i + content_blocks_per_result_set]
        rsp.content_block_count = len(content_blocks)

        if prp.collection.type == CT_DATA_FEED:  # Need to set timestamp label fields
            # Set the begin TS label
            # For the first part, use the exclusive begin timestamp label supplied as an arg,
            # as that's the exclusive begin timestmap label for the whole result set and
            # is not necessarily equal to the timestamp label of the first content block.
            # For all subsequent parts, use the timestamp label of the i-1 content block
            # as the exclusive begin timestamp label
            if part_number == 1:  # This is the first result set part
                rsp.exclusive_begin_timestamp_label = prp.exclusive_begin_timestamp_label
            else:  # This is not the first result set, use the i-1 Content Block's timestamp label
                rsp.exclusive_begin_timestamp_label = results[i - 1].timestamp_label

            # Set the end TS label
            # For the last part, use the inclusive end timestamp label supplied as an arg,
            # as that's the inclusive end timestamp label for the whole result set and
            # is not necessariy equal to the timestamp label of the last content block.
            # For all other parts, use the timestamp label of the last content block in the
            # result part.
            if i + content_blocks_per_result_set >= len(results):  # There won't be any more result parts
                rsp.inclusive_end_timestamp_label = prp.inclusive_end_timestamp_label
            else:  # There will be more result parts
                rsp.inclusive_end_timestamp_label = content_blocks[-1].timestamp_label

        if i + content_blocks_per_result_set >= len(results):  # This is the last result set part
            rsp.more = False
        else:
            rsp.more = True

        rsp.save()
        i += len(content_blocks)
        part_number += 1

        # Add content_blocks to the result set part
        for cb in content_blocks:
            rsp.content_blocks.add(cb)
        rsp.save()

    return result_set
