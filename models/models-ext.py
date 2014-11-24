


class CapabilityModule(_Tag):
    pass



class InboxMessage(models.Model):
    """
    Used to store information about received Inbox Messages
    """
    # TODO: What should I index on?
    # TODO: NONE of these fields should be editable in the admin, but they should all be viewable
    message_id = models.CharField(max_length=MAX_NAME_LENGTH)
    sending_ip = models.CharField(max_length=MAX_NAME_LENGTH)
    datetime_received = models.DateTimeField(auto_now_add=True)
    result_id = models.CharField(max_length=MAX_NAME_LENGTH, blank=True, null=True)

    # Record Count items
    record_count = models.IntegerField(blank=True, null=True)
    partial_count = models.BooleanField(default=False)

    # Subscription Information items
    collection_name = models.CharField(max_length=MAX_NAME_LENGTH, blank=True, null=True)
    subscription_id = models.CharField(max_length=MAX_NAME_LENGTH, blank=True, null=True)
    exclusive_begin_timestamp_label = models.DateTimeField(blank=True, null=True)
    inclusive_end_timestamp_label = models.DateTimeField(blank=True, null=True)

    received_via = models.ForeignKey('InboxService', blank=True, null=True)
    original_message = models.TextField(blank=True, null=True)
    content_block_count = models.IntegerField()
    content_blocks_saved = models.IntegerField()

    @staticmethod
    def from_inbox_message_10(inbox_message, django_request, received_via=None):
        """
        Creates an InboxMessage model object from a tm10.InboxMessage object.

        NOTE THAT THIS FUNCTION DOES NOT CALL .save()

        :param inbox_message: The tm10.InboxMessage to create as a DB object
        :param django_request: The django request that contained the inbox message
        :param receved_via: The inbox service this Inbox Message was received via
        :return: An **unsaved** models.InboxMessage object
        """

        inbox_message_db = InboxMessage()
        inbox_message_db.message_id = inbox_message.message_id
        inbox_message_db.sending_ip = django_request.META.get('REMOTE_ADDR', None)

        if inbox_message.subscription_information:
            si = inbox_message.subscription_information
            inbox_message_db.collection_name = si.feed_name
            inbox_message_db.subscription_id = si.subscription_id
            # TODO: Match up exclusive vs inclusive
            inbox_message_db.exclusive_begin_timestamp_label = si.inclusive_begin_timestamp_label
            inbox_message_db.inclusive_end_timestamp_label = si.inclusive_end_timestamp_label

        if received_via:
            inbox_message_db.received_via = received_via

        inbox_message_db.original_message = inbox_message.to_xml()
        inbox_message_db.content_block_count = len(inbox_message.content_blocks)
        inbox_message_db.content_blocks_saved = 0

        return inbox_message_db

    @staticmethod
    def from_inbox_message_11(inbox_message, django_request, received_via=None):
        """
        Create an InboxMessage model object
        from a tm11.InboxMessage object

        NOTE THAT THIS FUNCTION DOES NOT CALL .save()

        Returns:
            An **unsaved** models.InboxMessage object.
        """

        # For bookkeeping purposes, create an InboxMessage object
        # in the database
        inbox_message_db = InboxMessage()  # The database instance of the inbox message
        inbox_message_db.message_id = inbox_message.message_id
        inbox_message_db.sending_ip = django_request.META.get('REMOTE_ADDR', None)
        if inbox_message.result_id:
            inbox_message_db.result_id = inbox_message.result_id

        if inbox_message.record_count:
            inbox_message_db.record_count = inbox_message.record_count.record_count
            inbox_message_db.partial_count = inbox_message.record_count.partial_count

        if inbox_message.subscription_information:
            si = inbox_message.subscription_information
            inbox_message_db.collection_name = si.collection_name
            inbox_message_db.subscription_id = si.subscription_id
            if si.exclusive_begin_timestamp_label:
                inbox_message_db.exclusive_begin_timestamp_label = si.exclusive_begin_timestamp_label
            if si.inclusive_end_timestamp_label:
                inbox_message_db.inclusive_end_timestamp_label = si.inclusive_end_timestamp_label

        if received_via:
            inbox_message_db.received_via = received_via  # This is an inbox service

        inbox_message_db.original_message = inbox_message.to_xml()
        inbox_message_db.content_block_count = len(inbox_message.content_blocks)
        inbox_message_db.content_blocks_saved = 0

        return inbox_message_db

    def __unicode__(self):
        return u'%s - %s' % (self.message_id, self.datetime_received)

    class Meta:
        ordering = ['datetime_received']
        verbose_name = "Inbox Message"


class InboxService(_TaxiiService):
    """
    Model for a TAXII Inbox Service
    """
    service_type = SVC_INBOX
    inbox_message_handler = models.ForeignKey('MessageHandler',
                                              limit_choices_to={'supported_messages__contains':
                                                                'InboxMessage'})
    destination_collection_status = models.CharField(max_length=MAX_NAME_LENGTH, choices=ROP_CHOICES)
    destination_collections = models.ManyToManyField('DataCollection', blank=True)
    accept_all_content = models.BooleanField(default=False)
    supported_content = models.ManyToManyField('ContentBindingAndSubtype', blank=True, null=True)

    def get_message_handler(self, taxii_message):
        if taxii_message.message_type == MSG_INBOX_MESSAGE:
            return self.inbox_message_handler

        raise StatusMessageException(taxii_message.message_id,
                                     ST_FAILURE,
                                     message="Message not supported by this service")

    def is_content_supported(self, cbas):
        """
        Takes an ContentBindingAndSubtype object and determines if
        this data collection supports it.

        Decision process is:
        1. If this accepts any content, return True
        2. If this supports binding ID > (All), return True
        3. If this supports binding ID and subtype ID, return True
        4. Otherwise, return False,
        """

        # 1
        if self.accept_all_content:
            return SupportInfo(True, None)

        # 2
        if len(self.supported_content.filter(content_binding=cbas.content_binding, subtype=None)) > 0:
            return SupportInfo(True, None)

        # 2a (e.g., subtype = None so #3 would end up being the same check as #2)
        if not cbas.subtype:  # No further checking can be done
            return SupportInfo(False, None)

        # 3
        if len(self.supported_content.filter(content_binding=cbas.content_binding, subtype=cbas.subtype)) > 0:
            return SupportInfo(True, None)

        # 4
        return SupportInfo(False, None)

    def validate_destination_collection_names(self, name_list, in_response_to):
        """
        Returns:
            A list of Data Collections

        Raises:
            A StatusMessageException if any Destination Collection Names are invalid.
        """
        if name_list is None:
            name_list = []

        num = len(name_list)
        if self.destination_collection_status == REQUIRED[0] and num == 0:
            raise StatusMessageException(in_response_to,
                                         ST_DESTINATION_COLLECTION_ERROR,
                                         'A Destination_Collection_Name is required and none were specified',
                                         {SD_ACCEPTABLE_DESTINATION: [str(dc.name) for dc in self.destination_collections.all()]})

        if self.destination_collection_status == PROHIBITED[0] and num > 0:
            raise StatusMessageException(in_response_to,
                                         ST_DESTINATION_COLLECTION_ERROR,
                                         'Destination_Collection_Names are prohibited on this Inbox Service',
                                         {SD_ACCEPTABLE_DESTINATION: [str(dc.name) for dc in self.destination_collections.all()]})

        collections = []
        for name in name_list:
            try:
                collection = self.destination_collections.get(name=name, enabled=True)
                collections.append(collection)
            except:
                raise StatusMessageException(in_response_to,
                                             ST_NOT_FOUND,
                                             'The Data Collection was not found',
                                             {SD_ITEM: name})

        return collections

    def to_service_instances_10(self):
        service_instances = super(InboxService, self).to_service_instances_10()
        if self.accept_all_content:
            return service_instances

        for si in service_instances:
            si.accepted_contents = self.get_supported_content_10()
        return service_instances

    def to_service_instances_11(self):
        service_instances = super(InboxService, self).to_service_instances_10()
        if self.accept_all_content:
            return service_instances

        for si in service_instances:
            si.accepted_contents = self.get_supported_content_11()
        return service_instances

    def get_supported_content_10(self):
        return_list = []

        if self.accept_all_content:
            return_list = None  # Indicates accept all
        else:
            for content in self.supported_content.all():
                return_list.append(content.content_binding.binding_id)
        return return_list

    def get_supported_content_11(self):
        return_list = []

        if self.accept_all_content:
            return_list = None  # Indicates accept all
        else:
            supported_content = {}

            for content in self.supported_content.all():
                binding_id = content.content_binding.binding_id
                subtype = content.subtype
                if binding_id not in supported_content:
                    supported_content[binding_id] = tm11.ContentBinding(binding_id=binding_id)

                if subtype and subtype.subtype_id not in supported_content[binding_id].subtype_ids:
                    supported_content[binding_id].subtype_ids.append(subtype.subtype_id)

            return_list = supported_content.values()

        return return_list

    class Meta:
        verbose_name = "Inbox Service"


class MessageBinding(_BindingBase):
    """
    Represents a Message Binding, used to establish the supported syntax
    for a given TAXII exchange, "e.g., XML".

    Ex:
    XML message binding id : "urn:taxii.mitre.org:message:xml:1.1"
    """
    class Meta:
        verbose_name = "Message Binding"


class MessageHandler(_Handler):
    """
    MessageHandler model object.
    """
    handler_functions = ['handle_message']
    supported_messages = models.CharField(max_length=MAX_NAME_LENGTH, editable=False)

    def clean(self):
        handler_class = super(MessageHandler, self).clean()
        try:
            self.supported_messages = handler_class.get_supported_request_messages()
        except:
            raise ValidationError('There was a problem getting the list of supported messages: %s' %
                                  str(sys.exc_info()))

    class Meta:
        verbose_name = "Message Handler"


class PollService(_TaxiiService):
    """
    Model for a Poll Service
    """
    service_type = SVC_POLL
    poll_request_handler = models.ForeignKey('MessageHandler',
                                             related_name='poll_request',
                                             limit_choices_to={'supported_messages__contains':
                                                               'PollRequest'})
    poll_fulfillment_handler = models.ForeignKey('MessageHandler',
                                                 related_name='poll_fulfillment',
                                                 limit_choices_to={'supported_messages__contains':
                                                                   'PollFulfillmentRequest'},
                                                 blank=True,
                                                 null=True)
    data_collections = models.ManyToManyField('DataCollection')
    supported_queries = models.ManyToManyField('SupportedQuery', blank=True, null=True)
    requires_subscription = models.BooleanField(default=False)
    max_result_size = models.IntegerField(blank=True, null=True)  # Blank means "no limit"

    def clean(self):
        """
        Perform some validation on the model

        :return: Nothing
        """

        if self.max_result_size is not None and self.max_result_size < 1:
            raise ValidationError("Max Result Size must be blank or greater than 1!")

    def get_message_handler(self, taxii_message):
        if taxii_message.message_type == MSG_POLL_REQUEST:
            return self.poll_request_handler
        elif taxii_message.message_type == MSG_POLL_FULFILLMENT_REQUEST:
            return self.poll_fulfillment_handler

        raise StatusMessageException(taxii_message.message_id,
                                     ST_FAILURE,
                                     message="Message not supported by this service")

    def validate_collection_name(self, name, in_response_to):
        """
        Arguments:
            name (str) - The name of a Data Collection
            in_response_to (str) - The message_id to use if this function raises an Exception

        Returns:
            A DataCollection object based on the name

        Raises:
            A StatusMessageException if the named Data Collection does not exist
        """
        try:
            collection = self.data_collections.get(name=name)
        except DataCollection.DoesNotExist as dne:
            raise StatusMessageException(in_response_to,
                                         ST_NOT_FOUND,
                                         'The collection you requested was not found',
                                         {SD_ITEM: name})

        return collection

    def get_supported_query(self, query, in_response_to):
        """
        This function follows this workflow to find a matching query handler:
        TODO: Once the function works, document what it does

        Arguments:
            query - tdq.DefaultQuery object

        Returns:
            a QueryHandler for handling the query

        Raises:
            A StatusMessageException if a QueryHandler was not found
        """

        # 1. filter down by Targeting Expression ID
        tev_kwargs = {'query_handler__targeting_expression_ids__value': query.targeting_expression_id}
        potential_matches = self.supported_queries.filter(**tev_kwargs)

        if len(potential_matches) == 0:
            exprs = []
            for sq in self.supported_queries.all():
                for tev in sq.query_handler.targeting_expression_ids.all():
                    exprs.append(tev.value)

            raise StatusMessageException(in_response_to,
                                         ST_UNSUPPORTED_TARGETING_EXPRESSION_ID,
                                         status_detail={'TARGETING_EXPRESSION_ID': exprs})

        # Build the list of unique targets and capability modules used in the query
        targets = set([])  # Targets
        cms = set([])  # Capability Modules
        to_search = [query.criteria]

        while len(to_search) > 0:
            item = to_search.pop()
            try:
                targets.add(item.target)
                cms.add(item.test.capability_id)
            except AttributeError:
                to_search.extend(item.criteria)
                to_search.extend(item.criterion)

        for cm in cms:
            potential_matches = potential_matches.filter(query_handler__capability_modules__value=cm)
            if len(potential_matches) == 0:
                raise StatusMessageException(in_response_to,
                                             ST_UNSUPPORTED_CAPABILITY_MODULE,
                                             status_detail={SD_CAPABILITY_MODULE: ['TBD']})

        # Targets have to be checked in software (for now ... ?)
        list_potential_matches = list(potential_matches)
        # print 'looking at targets'
        for target in targets:
            for potential_match in list_potential_matches:
                tgt_support = potential_match.query_handler.get_handler_class().is_target_supported(target)
                if not tgt_support.is_supported:
                    list_potential_matches.remove(potential_match)
                    if len(list_potential_matches) == 0:
                        raise StatusMessageException(in_response_to,
                                                     ST_UNSUPPORTED_TARGETING_EXPRESSION,
                                                     message=tgt_support.message)
        # print 'done looking at targets'

        # We've found matches. Arbitrarily pick the first one.
        return list_potential_matches[0]

    def to_service_instances_11(self):
        service_instances = super(PollService, self).to_service_instances_11()

        for si in service_instances:
            for sq in self.supported_queries.all():
                si.supported_query.append(sq.to_query_info_11())
        return service_instances

    class Meta:
        verbose_name = "Poll Service"


class ProtocolBinding(_BindingBase):
    """
    Represents a Protocol Binding, used to establish the supported transport
    for a given TAXII exchange, "e.g., HTTP".

    Ex:
    HTTP Protocol Binding : "urn:taxii.mitre.org:protocol:http:1.0"
    """
    class Meta:
        verbose_name = "Protocol Binding"


class QueryHandler(_Handler):
    """
    A model for Query Handlers. A query handler is a function that
    takes two arguments: A query and a content block and returns
    True if the Content Block passes the query and False otherwise.
    """

    # TODO: Update this list
    handler_functions = ['get_supported_cms',
                         'get_supported_tevs',
                         #'is_scope_supported',
                         'is_target_supported',
                         'filter_content',
                         'update_db_kwargs']

    targeting_expression_ids = models.ManyToManyField('TargetingExpressionId', editable=False, blank=True, null=True)
    capability_modules = models.ManyToManyField('CapabilityModule', editable=False, blank=True, null=True)

    def clean(self):
        handler_class = super(QueryHandler, self).clean()

    def is_tev_supported(self, tev):
        """
        tev is short for targeting expression vocabulary
        :param tev: (string) A targeting expression vocabulary identifier (ID)
        :return: A SupportInfo object indicating whether the tev is supported.
        """
        return self.get_handler_class().is_tev_supported(tev)

    def is_te_supported(self, te):
        """
        :param te: (string) A targeting expression
        :return: A SupportInfo object indicating whether the targeting expression is supported
        """
        return self.get_handler_class().is_te_supported(te)

    def is_cm_supported(self, cm):
        """
        :param cm: (string) A Capability Module ID
        :return: A SupportInfo object indicating whether the capability module is supported
        """
        return self.get_handler_class().is_cm_supported(cm)

    class Meta:
        verbose_name = "Query Handler"


#class QueryHandlerCapabilityModule(models.Model):
#    """
#    Assists in managing the QueryHandler/CapabilityModule relationships
#    """
#    query_handler = models.ForeignKey('QueryHandler')
#    capability_module = models.ForeignKey('CapabilityModule')


def update_query_handler(sender, **kwargs):
    """
    When a QueryHandler gets created, CapabilityModules is a M2M and can't
    be saved when the model is saved.
    """
    instance = kwargs['instance']
    handler_class = instance.get_handler_class()
    for cm in handler_class.get_supported_cms():
        cm_obj = CapabilityModule.objects.get(value=cm)
        instance.capability_modules.add(cm_obj)

    for tev in handler_class.get_supported_tevs():
        tev_obj = TargetingExpressionId.objects.get(value=tev)
        instance.targeting_expression_ids.add(tev_obj)

post_save.connect(update_query_handler, sender=QueryHandler)


class ResultSet(models.Model):
    """
    Model for Result Sets
    """
    data_collection = models.ForeignKey('DataCollection')
    subscription = models.ForeignKey('Subscription', blank=True, null=True)
    total_content_blocks = models.IntegerField()
    # TODO: Figure out how to limit choices to only the ResultSetParts that belong to this ResultSet
    last_part_returned = models.ForeignKey('ResultSetPart', blank=True, null=True)
    expires = models.DateTimeField()
    # TODO: There's nothing in here for pushing. It should be added
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'ResultSet ID: %s; Collection: %s; Parts: %s.' % \
               (self.id, self.data_collection, self.resultsetpart_set.count())

    class Meta:
        verbose_name = "Result Set"


class ResultSetPart(models.Model):
    """
    Model for Result Set Parts
    """
    result_set = models.ForeignKey('ResultSet')
    part_number = models.IntegerField()
    content_blocks = models.ManyToManyField('ContentBlock')
    content_block_count = models.IntegerField()
    more = models.BooleanField(default=False)
    exclusive_begin_timestamp_label = models.DateTimeField(blank=True, null=True)
    inclusive_end_timestamp_label = models.DateTimeField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'ResultSet ID: %s; Collection: %s; Part#: %s.' % \
               (self.result_set.id, self.result_set.data_collection, self.part_number)

    def to_poll_response_11(self, in_response_to):
        """
        Returns a tm11.PollResponse based on this model
        """

        poll_response = tm11.PollResponse(message_id=tm11.generate_message_id(),
                                          in_response_to=in_response_to,
                                          collection_name=self.result_set.data_collection.name)

        if self.exclusive_begin_timestamp_label:
            poll_response.exclusive_begin_timestamp_label = self.exclusive_begin_timestamp_label

        if self.inclusive_end_timestamp_label:
            poll_response.inclusive_end_timestamp_label = self.inclusive_end_timestamp_label

        if self.result_set.subscription:
            poll_response.subscription_id = self.result_set.subscription.subscription_id

        poll_response.record_count = tm11.RecordCount(self.result_set.total_content_blocks, False)
        poll_response.more = self.more
        poll_response.result_id = str(self.result_set.pk)
        poll_response.result_part_number = self.part_number

        for content_block in self.content_blocks.all():
            cb = content_block.to_content_block_11()
            poll_response.content_blocks.append(cb)

        return poll_response

    class Meta:
        verbose_name = "Result Set Part"
        unique_together = ('result_set', 'part_number',)


class Subscription(models.Model):
    """
    Model for Subscriptions
    """
    subscription_id = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    data_collection = models.ForeignKey('DataCollection')
    response_type = models.CharField(max_length=MAX_NAME_LENGTH, choices=RESPONSE_CHOICES, default=RT_FULL)
    accept_all_content = models.BooleanField(default=False)
    supported_content = models.ManyToManyField('ContentBindingAndSubtype', blank=True, null=True)
    query = models.TextField(blank=True)
    # push_parameters = models.ForeignKey(PushParameters)  # TODO: Create a push parameters object
    delivery = models.CharField(max_length=MAX_NAME_LENGTH, choices=DELIVERY_CHOICES, default=SUBS_POLL)
    status = models.CharField(max_length=MAX_NAME_LENGTH, choices=SUBSCRIPTION_STATUS_CHOICES, default=SS_ACTIVE)
    date_paused = models.DateTimeField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def validate_active(self, in_response_to):
        """
        If the status is not active, raises a StatusMessageException.
        Otherwise, has no effect
        """
        if not self.status == SS_ACTIVE:
            raise StatusMessageException(in_response_to,
                                         ST_FAILURE,
                                         'The Subscription is not active!')

    def to_poll_params_11(self):
        """
        Creates a tm11.PollParameters object based on the
        properties of this Subscription.
        """
        pp = tm11.PollParameters(response_type=self.response_type,
                                 content_bindings=self.supported_content.all(),  # Get supported contents?
                                 allow_asynch=False,  # TODO: This can't be specified?
                                 # delivery_parameters = self.push_parameters)
                                 query=self.query)  # ,  # TODO: Implement push_parameters
        return pp

    def to_subscription_instance_10(self):
        """
        Returns a tm10.SubscriptionInstance object
        based on this model
        """
        push_params = None  # TODO: Implement this
        poll_instances = None  # TODO: Implement this

        si = tm10.SubscriptionInstance(subscription_id=self.subscription_id,
                                       push_parameters=push_params,
                                       poll_instances=poll_instances)
        return si

    def to_subscription_instance_11(self):
        """
        Returns a tm11.SubscriptionInstance object based on this
        model
        """
        subscription_params = tm11.SubscriptionParameters(response_type=self.response_type,
                                                          content_bindings=self.get_supported_content(self))

        if self.query:
            subscription_params.query = self.query.to_query_11()

        push_params = None  # TODO: Implement this
        poll_instances = None  # TODO: Implement this

        si = tm11.SubscriptionInstance(subscription_id=self.subscription_id,
                                       status=self.status,
                                       subscription_parameters=subscription_params,
                                       push_parameters=push_params,
                                       poll_instances=poll_instances)
        return si

    def __unicode__(self):
        return u'Subscription ID: %s' % self.subscription_id


class SupportedQuery(models.Model):
    """
    A SupportedQuery Object represents a QueryHandler plus
    an (optional, user-configurable) scope restriction of that
    QueryHandler.
    """
    name = models.CharField(max_length=MAX_NAME_LENGTH)
    description = models.TextField(blank=True)

    query_handler = models.ForeignKey('QueryHandler')
    use_handler_scope = models.BooleanField(default=True)
    preferred_scope = models.ManyToManyField('QueryScope', blank=True, null=True, related_name='preferred_scope')
    allowed_scope = models.ManyToManyField('QueryScope', blank=True, null=True, related_name='allowed_scope')

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def is_query_supported(self, query):
        """
        :param query: a libtaxii.taxii_default_query.DefaultQuery object
        :return: A SupportInfo object indicating whether the Query is supported.
        """

        # If the Targeting Expression Vocabulary Identifier is not supported, indicate that
        tev_supp_info = self.is_tev_supported(query.targeting_expression_id)
        if tev_supp_info.is_supported is False:
            return tev_supp_info

        # Build the list of unique targets and capability modules used in the query
        targets = set([])  # Targets
        cms = set([])  # Capability Modules
        to_search = [query.criteria]

        while len(to_search) > 0:
            item = to_search.pop()
            try:
                targets.add(item.target)
                cms.add(item.test.capability_id)
            except AttributeError:
                to_search.extend(item.criteria)
                to_search.extend(item.criterion)

        for cm in cms:
            cm_supp_info = self.is_cm_supported(cm)
            if cm_supp_info.is_supported is False:
                return cm_supp_info

        for target in targets:
            tgt_supp_info = self.is_target_supported(target)
            if tgt_supp_info.is_supported is False:
                return tgt_supp_info

        return SupportInfo(is_supported=True)

    def is_tev_supported(self, tev):
        """
        :param tev: (string) A targeting expression vocabulary id
        :return: A SupportInfo object indicating whether the targeting expression vocabulary ID is supported
        """

        # Note: This function primarily exists to provide a future hook

        return self.query_handler.is_tev_supported()

    def is_cm_supported(self, cm):
        """
        :param cm: (string) A capability module id
        :return: a SupportInfo object indicating whether the capability module id is supported
        """

        # Note: This function primarily exists to provide a future hook

        return self.query_handler.is_cm_supported()

    def is_target_supported(self, target):
        """
        :param target: (string) A target
        :return: A SupportInfo object indicating whether the target is supported
        """
        if self.use_handler_scope is True:
            return self.query_handler.is_target_supported(target)
        else:
            raise NotImplementedError("UI Based restrictions of query handler not implemented yet!")

    def to_query_info_11(self):
        """
        Returns a tdq.QueryInfo object
        based on this model
        """
        preferred_scope = [ps.scope for ps in self.preferred_scope.all()]
        allowed_scope = [as_.scope for as_ in self.allowed_scope.all()]
        targeting_expression_id = self.query_handler.targeting_expression_id

        tei = tdq.DefaultQueryInfo.TargetingExpressionInfo(targeting_expression_id=targeting_expression_id,
                                                           preferred_scope=preferred_scope,
                                                           allowed_scope=allowed_scope)

        # TODO: I don't think commas are permitted, but they'd break this processing
        # Probably fix that, maybe through DB field validation
        # This is stored in the DB as a python list, so get rid of all the "extras"
        map_ = dict((ord(char), None) for char in " []\'")
        cm_list = self.query_handler.capability_modules.translate(map_).split(',')

        dqi = tdq.DefaultQueryInfo(targeting_expression_infos=[tei],
                                   capability_modules=cm_list)
        return dqi

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = "Supported Query"
        verbose_name_plural = "Supported Queries"


class TargetingExpressionId(_Tag):
    pass


class Validator(_Handler):
    """
    Model for Validators. A Validator, at the moment,
    is an idea only. Eventually, it would be nice to be
    able to have content that comes in be passed to an
    automatic validator before storage.

    At some point, if a validator gets invented, this
    model will leverage that validator concept.
    """
    handler_functions = ['validate']
