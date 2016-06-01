from libtaxii import messages_10 as tm10
from libtaxii import messages_11 as tm11

from opentaxii.taxii import entities
from opentaxii.taxii.http import (
    TAXII_10_HTTPS_Headers, TAXII_10_HTTP_Headers, TAXII_11_HTTPS_Headers,
    TAXII_11_HTTP_Headers
)
from opentaxii.taxii.http import (
    HTTP_ACCEPT, HTTP_CONTENT_XML)

from opentaxii.taxii.utils import get_utc_now

from fixtures import (
    CB_STIX_XML_111, CONTENT, MESSAGE, MESSAGE_ID)


def as_tm(version):
    if version == 10:
        return tm10
    elif version == 11:
        return tm11
    else:
        raise ValueError('Unknown TAXII message version: %s' % version)


def prepare_headers(version, https):
    headers = dict()
    if version == 10:
        if https:
            headers.update(TAXII_10_HTTPS_Headers)
        else:
            headers.update(TAXII_10_HTTP_Headers)
    elif version == 11:
        if https:
            headers.update(TAXII_11_HTTPS_Headers)
        else:
            headers.update(TAXII_11_HTTP_Headers)
    else:
        raise ValueError('Unknown TAXII message version: %s' % version)

    headers[HTTP_ACCEPT] = HTTP_CONTENT_XML
    return headers


def persist_content(manager, collection_name, service_id, timestamp=None,
                    binding=CB_STIX_XML_111, subtypes=[]):

    timestamp = timestamp or get_utc_now()

    content_binding = entities.ContentBindingEntity(
        binding=binding,
        subtypes=subtypes
    )

    content = entities.ContentBlockEntity(
        content=CONTENT, timestamp_label=timestamp,
        message=MESSAGE, content_binding=content_binding)

    collection = manager.get_collection(collection_name, service_id)

    if not collection:
        raise ValueError('No collection with name {}'.format(collection_name))

    content = manager.create_content(content, collections=[collection])

    return content


def prepare_subscription_request(collection, action, version,
                                 subscription_id=None, params=None):

    data = dict(
        action=action,
        message_id=MESSAGE_ID,
        subscription_id=subscription_id,
    )

    mod = as_tm(version)

    if version == 11:
        cls = mod.ManageCollectionSubscriptionRequest
        data.update(dict(
            collection_name=collection,
            subscription_parameters=(
                mod.SubscriptionParameters(**params) if params else None)
        ))
    else:
        cls = mod.ManageFeedSubscriptionRequest
        data['feed_name'] = collection

    return cls(**data)


def includes(superset, subset):
    return all(item in superset.items() for item in subset.items())


def is_headers_valid(headers, version, https):
    if version == 10:
        if https:
            return includes(headers, TAXII_10_HTTPS_Headers)
        else:
            return includes(headers, TAXII_10_HTTP_Headers)
    elif version == 11:
        if https:
            return includes(headers, TAXII_11_HTTPS_Headers)
        else:
            return includes(headers, TAXII_11_HTTP_Headers)
    else:
        raise ValueError('Unknown TAXII message version: %s' % version)
