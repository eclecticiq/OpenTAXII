import pytz
from datetime import datetime

from libtaxii.constants import *
from libtaxii import messages_11 as tm11

from .exceptions import StatusMessageException


def get_utc_now():
    return datetime.utcnow().replace(tzinfo=pytz.UTC)


def is_content_supported(supported_bindings, content_binding, version=None):

    if not hasattr(content_binding, 'binding_id') or version == 10:
        binding_id = content_binding
        subtype = None
    else:
        binding_id = content_binding.binding_id
        subtype = content_binding.subtype_ids[0] if content_binding.subtype_ids else None #FIXME: may be not the best option

    matches = [
        ((supported.binding == binding_id) and (not supported.subtypes or subtype in supported.subtypes)) \
        for supported in supported_bindings
    ]

    return any(matches)


def prepare_supported_content(supported_content, version):
    return_list = []

    if version == 10:
        for content in supported_content:
            return_list.append(content.binding)

    elif version == 11:
        bindings = {}

        for content in supported_content:
            if content.binding not in bindings:
                bindings[content.binding] = tm11.ContentBinding(binding_id=content.binding, subtype_ids=content.subtypes)

        return_list = bindings.values()

    return return_list



def content_bindings_intersection(supported_bindings, requested_bindings):

    if not supported_bindings:
        return requested_bindings

    if not requested_bindings:
        return supported_bindings

    overlap = []

    for requested in requested_bindings:
        for supported in supported_bindings:

            if requested.binding != supported.binding:
                continue

            if not supported.subtypes:
                overlap.append(requested)
                continue

            if not requested.subtypes:
                overlap.append(supported)
                continue

            subtypes_overlap = set(supported.subtypes).intersection(requested.subtypes)

            overlap.append(ContentBinding(
                binding = request.binding, 
                subtypes = subtypes_overlap
            ))

    return overlap

