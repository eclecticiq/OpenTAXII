import json
import pytz

from opentaxii.taxii import entities


def to_collection_entity(model):
    if not model:
        return
    return entities.CollectionEntity(
        id=model.id,
        name=model.name,
        available=model.available,
        type=model.type,
        description=model.description,
        accept_all_content=model.accept_all_content,
        supported_content=deserialize_content_bindings(model.bindings),
        # TODO: Explicit integer
        # pending: https://github.com/TAXIIProject/libtaxii/issues/191
        volume=int(model.volume)
    )


def to_block_entity(model):
    if not model:
        return

    subtypes = [model.binding_subtype] if model.binding_subtype else None

    return entities.ContentBlockEntity(
        id=model.id,
        content=model.content,
        timestamp_label=enforce_timezone(model.timestamp_label),
        content_binding=entities.ContentBindingEntity(
            model.binding_id, subtypes=subtypes),
        message=model.message,
        inbox_message_id=model.inbox_message_id,
    )


def to_inbox_message_entity(model):
    if not model:
        return

    if model.destination_collections:
        names = json.loads(model.destination_collections)
    else:
        names = []

    return entities.InboxMessageEntity(
        id=model.id,
        message_id=model.message_id,
        original_message=model.original_message,
        content_block_count=model.content_block_count,
        destination_collections=names,

        service_id=model.service_id,

        result_id=model.result_id,
        record_count=model.record_count,
        partial_count=model.partial_count,

        subscription_collection_name=model.subscription_collection_name,
        subscription_id=model.subscription_id,

        exclusive_begin_timestamp_label=enforce_timezone(
            model.exclusive_begin_timestamp_label),
        inclusive_end_timestamp_label=enforce_timezone(
            model.inclusive_end_timestamp_label),
    )


def to_result_set_entity(model):
    if not model:
        return
    return entities.ResultSetEntity(
        id=model.id,
        collection_id=model.collection_id,
        content_bindings=deserialize_content_bindings(model.bindings),
        timeframe=(
            enforce_timezone(model.begin_time),
            enforce_timezone(model.end_time))
    )


def to_subscription_entity(model):
    if not model:
        return

    if model.params:
        parsed = dict(json.loads(model.params))
        if parsed['content_bindings']:
            parsed['content_bindings'] = deserialize_content_bindings(
                parsed['content_bindings'])
        params = entities.PollRequestParametersEntity(**parsed)
    else:
        params = None

    return entities.SubscriptionEntity(
        service_id=model.service_id,
        subscription_id=model.id,
        collection_id=model.collection_id,
        poll_request_params=params,
        status=model.status
    )


def to_service_entity(model):
    if not model:
        return
    return entities.ServiceEntity(
        id=model.id,
        type=model.type,
        properties=model.properties)


def serialize_content_bindings(content_bindings):
    return json.dumps([(c.binding, c.subtypes) for c in content_bindings])


def deserialize_content_bindings(content_bindings):
    raw_bindings = json.loads(content_bindings)

    bindings = []
    for (binding, subtypes) in raw_bindings:
        entity = entities.ContentBindingEntity(binding, subtypes=subtypes)
        bindings.append(entity)

    return bindings


# SQLite does not preserve TZ information
def enforce_timezone(date):

    if not date:
        return

    if date.tzinfo:
        return date

    return date.replace(tzinfo=pytz.UTC)
