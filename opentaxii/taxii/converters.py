import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10

from libtaxii.constants import (
    SVC_COLLECTION_MANAGEMENT, SVC_FEED_MANAGEMENT,
    VID_TAXII_SERVICES_10, VID_TAXII_SERVICES_11
)

from .entities import (
    ContentBindingEntity, InboxMessageEntity, ContentBlockEntity,
    ServiceEntity
)


def parse_content_binding(raw_content_binding, version):
    if version == 10:
        return ContentBindingEntity(
            binding=raw_content_binding,
            subtypes=None)
    elif version == 11:
        return ContentBindingEntity(
            binding=raw_content_binding.binding_id,
            subtypes=raw_content_binding.subtype_ids)


def parse_content_bindings(bindings, version):
    return [parse_content_binding(b, version) for b in bindings]


def content_binding_entity_to_content_binding(content_binding, version):
    if version == 10:
        return content_binding.binding
    elif version == 11:
        return tm11.ContentBinding(
            binding_id=content_binding.binding,
            subtype_ids=content_binding.subtypes)


def content_binding_entities_to_content_bindings(content_bindings, version):
    return [
        content_binding_entity_to_content_binding(c, version)
        for c in content_bindings]


def service_to_service_instances(service, version):
    service_instances = []

    for binding in service.supported_protocol_bindings:
        address = service.get_absolute_address(binding)

        if version == 10:

            stype = service.service_type
            if stype == SVC_COLLECTION_MANAGEMENT:
                stype = SVC_FEED_MANAGEMENT

            instance = tm10.ServiceInstance(
                service_type=stype,
                services_version=VID_TAXII_SERVICES_10,
                available=service.available,
                protocol_binding=binding,
                service_address=address,
                message_bindings=service.supported_message_bindings,
                message=service.description
            )
        elif version == 11:
            instance = tm11.ServiceInstance(
                service_type=service.service_type,
                services_version=VID_TAXII_SERVICES_11,
                available=service.available,
                protocol_binding=binding,
                service_address=address,
                message_bindings=service.supported_message_bindings,
                message=service.description
            )
        service_instances.append(instance)

    return service_instances


# PollingServiceInstance vs PollInstance
def poll_service_to_polling_service_instance(service, version,
                                             is_poll_instance_cls=False):

    instances = []

    module = tm11 if version == 11 else tm10

    if is_poll_instance_cls:
        cls = module.PollInstance
    else:
        cls = module.PollingServiceInstance

    for binding in service.supported_protocol_bindings:
        address = service.get_absolute_address(binding)
        instance = cls(
            poll_protocol=binding,
            poll_address=address,
            poll_message_bindings=service.supported_message_bindings)

        instances.append(instance)

    return instances


def subscription_service_to_subscription_method(service, version):

    instances = []

    module = tm11 if version == 11 else tm10

    for binding in service.supported_protocol_bindings:
        address = service.get_absolute_address(binding)
        instance = module.SubscriptionMethod(
            subscription_protocol=binding,
            subscription_address=address,
            subscription_message_bindings=service.supported_message_bindings
        )
        instances.append(instance)

    return instances


def inbox_to_receiving_inbox_instance(inbox):
    inbox_instances = []

    for protocol_binding in inbox.supported_protocol_bindings:

        inbox_instances.append(tm11.ReceivingInboxService(
            inbox_protocol=protocol_binding,
            inbox_address=inbox.get_absolute_address(protocol_binding),
            inbox_message_bindings=inbox.supported_message_bindings,
            supported_contents=inbox.get_supported_content(version=11)
        ))

    return inbox_instances


def collection_to_feedcollection_information(service, collection, version):

    polling_instances = []
    for poll in service.get_polling_services(collection):
        polling_instances.extend(
            poll_service_to_polling_service_instance(poll, version=version))

    push_methods = service.get_push_methods(collection)

    subscription_methods = []
    for s in service.get_subscription_services(collection):
        subscription_methods.extend(
            subscription_service_to_subscription_method(s, version=version))

    if collection.accept_all_content:
        supported_content = []
    else:
        supported_content = content_binding_entities_to_content_bindings(
            collection.supported_content, version=version)

    if version == 11:
        inbox_instances = []
        for inbox in service.get_receiving_inbox_services(collection):
            inbox_instances.extend(inbox_to_receiving_inbox_instance(inbox))

        return tm11.CollectionInformation(
            collection_name=collection.name,
            collection_description=collection.description,
            supported_contents=supported_content,
            available=collection.available,

            push_methods=push_methods,
            polling_service_instances=polling_instances,
            subscription_methods=subscription_methods,

            collection_volume=collection.volume,
            collection_type=collection.type,
            receiving_inbox_services=inbox_instances
        )
    else:

        return tm10.FeedInformation(
            feed_name=collection.name,
            feed_description=collection.description,
            supported_contents=supported_content,
            available=collection.available,

            push_methods=push_methods,
            polling_service_instances=polling_instances,
            subscription_methods=subscription_methods
            # collection_volume, collection_type, and
            # receiving_inbox_services are not supported in TAXII 1.0
        )


def subscription_to_subscription_instance(subscription, polling_services,
                                          version,
                                          subscription_parameters=None):

    polling_instances = []
    for poll in polling_services:
        polling_instances.extend(
            poll_service_to_polling_service_instance(
                poll, version=version, is_poll_instance_cls=True))

    params = dict(
        subscription_id=subscription.subscription_id,
        poll_instances=polling_instances,
    )

    if version == 11:
        push_params = None

        params.update(dict(
            status=subscription.status,
            push_parameters=push_params,
        ))

        if subscription_parameters:
            bindings = content_binding_entities_to_content_bindings(
                subscription_parameters.content_bindings, version=version)

            params['subscription_parameters'] = tm11.SubscriptionParameters(
                response_type=subscription_parameters.response_type,
                content_bindings=bindings
            )

        return tm11.SubscriptionInstance(**params)
    else:
        params['delivery_parameters'] = None
        return tm10.SubscriptionInstance(**params)


def inbox_message_to_inbox_message_entity(inbox_message, service_id, version):

    params = dict(
        message_id=inbox_message.message_id,

        # FIXME: how to get raw value?
        original_message=inbox_message.to_xml(),
        content_block_count=len(inbox_message.content_blocks),
        service_id=service_id
    )

    if version == 10:

        if inbox_message.subscription_information:
            si = inbox_message.subscription_information
            begin = si.inclusive_begin_timestamp_label
            end = si.inclusive_end_timestamp_label
            params.update(dict(
                subscription_collection_name=si.feed_name,
                subscription_id=si.subscription_id,

                # TODO: Match up exclusive vs inclusive
                exclusive_begin_timestamp_label=begin,
                inclusive_end_timestamp_label=end
            ))

    elif version == 11:

        params.update(dict(
            result_id=inbox_message.result_id,
            destination_collections=inbox_message.destination_collection_names,
        ))

        if inbox_message.record_count:
            params.update(dict(
                record_count=inbox_message.record_count.record_count,
                partial_count=inbox_message.record_count.partial_count
            ))

        if inbox_message.subscription_information:
            si = inbox_message.subscription_information

            begin = si.exclusive_begin_timestamp_label
            end = si.inclusive_end_timestamp_label

            params.update(dict(
                subscription_collection_name=si.collection_name,
                subscription_id=si.subscription_id,
                exclusive_begin_timestamp_label=begin,
                inclusive_end_timestamp_label=end
            ))

    return InboxMessageEntity(**params)


def content_block_to_content_block_entity(content_block, version,
                                          inbox_message_id=None):

    content_binding = parse_content_binding(
        content_block.content_binding,
        version=version)

    message = content_block.message if version == 11 else None

    # TODO: What about signatures?
    return ContentBlockEntity(
        id=None,
        message=message,
        inbox_message_id=inbox_message_id,
        content=content_block.content,
        timestamp_label=content_block.timestamp_label,
        content_binding=content_binding
        # padding = content_block.padding,
    )


def content_block_entity_to_content_block(entity, version):

    content_bindings = content_binding_entity_to_content_binding(
        entity.content_binding,
        version=version)

    if version == 10:
        return tm10.ContentBlock(
            content_binding=content_bindings,
            content=entity.content,
            timestamp_label=entity.timestamp_label,
        )

    elif version == 11:
        return tm11.ContentBlock(
            content_binding=content_bindings,
            content=entity.content,
            timestamp_label=entity.timestamp_label,
            message=entity.message,
        )


def blob_to_service_entity(blob):

    properties = dict(blob)
    _id = properties.pop('id')
    _type = properties.pop('type')

    return ServiceEntity(id=_id, type=_type, properties=properties)
