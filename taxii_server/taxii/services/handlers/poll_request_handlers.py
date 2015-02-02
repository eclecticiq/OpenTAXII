
from .base_handlers import BaseMessageHandler
from ..exceptions import StatusMessageException
from ..utils import PollRequestProperties

import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
from libtaxii.constants import *
from libtaxii.common import generate_message_id

from datetime import timedelta


class PollRequest11Handler(BaseMessageHandler):
    """
    Built-in TAXII 1.1 Poll Request Handler.

    This handler has multiple extension points for developers
    who want to extend and/or customize this class.
    """

    supported_request_messages = [tm11.PollRequest]
    version = "1"

    @classmethod
    def get_content(cls, prp, query_kwargs):
        """
        Given a poll_params_dict get content from the database.

        Arguments:
            prp (util.PollRequestProperties) - Not used in this function, \
                    but can be used by implementers extending this function.
            query_kwargs (dict) - The parameters of the search for content

        Returns:
            An list of models.ContentBlock objects. Classes that override \
            this method only need to return an iterable where each class has \
            a 'to_content_block_11()' function.
        """
        content = prp.collection.content_blocks.filter(**query_kwargs).order_by('timestamp_label')

        return content

    @classmethod
    def create_poll_response(cls, poll_service, prp, content):
        """
        Creates a poll response.

        1. If the request's response type is "Count Only",
        a single poll response w/ more=False used.
        2. If the content size is less than the poll_service's
        max_result_size, a poll response w/ more=False is used.
        3. If the poll_service's max_result_size is blank,
        a poll response w/ more=False used.
        4. If the response type is "Full" and the total
        number of contents are greater than the
        poll_service's max_result_size, a ResultSet
        is created, and a PollResponse w/more=True is used.
        """

        content_count = len(content)

        # RT_COUNT_ONLY - Always use a single result
        # RT_FULL - Use a single response if
        #           poll_service.max_result_size is None or
        #           len(content) <= poll_service.max_result_size
        #           Use a Multi-Part response otherwise

        if (prp.response_type == RT_COUNT_ONLY or
            poll_service.max_result_size is None or
            content_count <= poll_service.max_result_size):

            poll_response = tm11.PollResponse(message_id=generate_message_id(),
                                              in_response_to=prp.message_id,
                                              collection_name=prp.collection.name,
                                              result_part_number=1,
                                              more=False,
                                              exclusive_begin_timestamp_label=prp.exclusive_begin_timestamp_label,
                                              inclusive_end_timestamp_label=prp.inclusive_end_timestamp_label,
                                              record_count=tm11.RecordCount(content_count, False))
            if prp.subscription:
                    poll_response.subscription_id = prp.subscription.subscription_id

            if prp.response_type == RT_FULL:
                for c in content:
                    poll_response.content_blocks.append(c.to_content_block_11())
        else:
            # Split into multiple result sets
            result_set = handlers.create_result_set(poll_service, prp, content)
            rsp_1 = models.ResultSetPart.objects.get(result_set__pk=result_set.pk, part_number=1)
            poll_response = rsp_1.to_poll_response_11(prp.message_id)
            result_set.last_part_returned = rsp_1
            result_set.save()
            response = poll_response

        return poll_response

    @classmethod
    def create_pending_response(cls, poll_service, prp, content):
        """
        Arguments:
            poll_service (models.PollService) - The TAXII Poll Service being invoked
            prp (util.PollRequestProperties) - The Poll Request Properties of the Poll Request
            content - A list of content (nominally, models.ContentBlock objects).

        This method returns a StatusMessage with a Status Type
        of Pending OR raises a StatusMessageException
        based on the following table::

            asynch | Delivery_Params | can_push || Response Type
            ----------------------------------------------------
            True   | -               | -        || Pending - Asynch
            False  | Yes             | Yes      || Pending - Push
            False  | Yes             | No       || StatusMessageException
            False  | No              | -        || StatusMessageException
        """

        # Identify the Exception conditions first (e.g., rows #3 and #4)
        if (prp.allow_asynch is False and
            (prp.delivery_parameters is None or prp.can_push is False)):

            raise StatusMessageException(prp.message_id,
                                         ST_FAILURE,
                                         "The content was not available now and \
                                         the request had allow_asynch=False and no \
                                         Delivery Parameters were specified.")

        # Rows #1 and #2 are both Status Messages with a type of Pending
        result_set = cls.create_result_set(content, prp, poll_service)
        sm = tm11.StatusMessage(message_id=generate_message_id(),
                                in_response_to=prp.message_id,
                                status_type=ST_PENDING)
        if prp.allow_asynch:
            sm.status_details = {SD_ESTIMATED_WAIT: 300, SD_RESULT_ID: result_set.pk, SD_WILL_PUSH: False}
        else:
            # TODO: Check and see if the requested delivery parameters are supported
            sm.status_details = {SD_ESTIMATED_WAIT: 300, SD_RESULT_ID: result_set.pk, SD_WILL_PUSH: True}
            # TODO: Need to try pushing or something.
        return sm

    @classmethod
    def handle_message(cls, poll_service, poll_request, django_request):
        """
        Handles a TAXII 1.1 Poll Request.

        Workflow:
            1. Create a util.PollRequestProperties object from the tm11.PollRequest
            2. If a Query Handler exists, call the `QueryHandler.update_db_kwargs( ... )`
               method of the Query Handler. This allows the QueryHandler a hook to modify the
               database query arguments before the query is sent do the database.
            3. Call `content = cls.get_content(PollRequestProperties, db_kwargs)`, which returns a list of
               objects, each of which must have a `to_content_block_11()` function.
            4. If a Query Handler exists, call the `QueryHandler.filter_content( ... )`
               function. This allows the QueryHandler a hook to modify the results after they have been returned
               from the database, but before they are returned to the requestor.
            5. If the results are available "now", return the result of calling
               `create_poll_response`.
            6. (Experimental) If the results are not available "now", return the result
                of calling `create_pending_response`.
        """
        # Populate a PollRequestProperties object from the poll request
        # A lot of magic happens in this function call
        prp = PollRequestProperties.from_poll_request_11(poll_service, poll_request)
        supported_query = prp.supported_query

        # Get the kwargs to search the DB with
        db_kwargs = prp.get_db_kwargs()

        # If a query handler exists, allow it to
        # inject kwargs
        if supported_query is not None:
            supported_query.query_handler.get_handler_class().update_db_kwargs(prp, db_kwargs)

        # Get content from the database.
        # content MUST be an iterable where each
        # object has a `to_content_block_11()` function
        content_blocks = cls.get_content(prp, db_kwargs)

        # If there is a query handler,
        # allow it do to post-dbquery filtering
        if supported_query:
            content_blocks = supported_query.query_handler.get_handler_class().filter_content(prp, content_blocks)

        # The way this handler is written, this will never be false
        results_available = True  # TODO: Can this flag be usefully implemented?

        if results_available:
            response = cls.create_poll_response(poll_service, prp, content_blocks)
        else:
            response = cls.create_pending_response(poll_service, prp, content_blocks)

        return response


class PollRequest10Handler(BaseMessageHandler):
    """
    Built-in TAXII 1.0 Poll Request Handler
    """
    supported_request_messages = [tm10.PollRequest]
    version = "1"

    @classmethod
    def get_content(cls, prp, query_kwargs):
        """

        :param prp: PollRequestProperties
        :param query_kwargs: The parameters of the search for content
        :return: A list of models.ContentBlock objects. Classes that override this  \
                 method only need to return an iterable where each instance has a \
                 'to_content_block_10()' function.
        """
        content = prp.collection.content_blocks.filter(**query_kwargs).order_by('timestamp_label')

        return content

    @classmethod
    def create_poll_response(cls, poll_service, prp, content_blocks):
        """

        :param poll_service:
        :param prp:
        :param content_blocks:
        :return:
        """

        ietl = prp.exclusive_begin_timestamp_label
        if ietl is not None:
            ietl += timedelta(milliseconds=1)

        pr = tm10.PollResponse(message_id=generate_message_id(),
                               in_response_to=prp.message_id,
                               feed_name=prp.collection.name,
                               inclusive_begin_timestamp_label=ietl,
                               inclusive_end_timestamp_label=prp.inclusive_end_timestamp_label)

        for content_block in content_blocks:
            pr.content_blocks.append(content_block.to_content_block_10())

        return pr

    @classmethod
    def handle_message(cls, poll_service, poll_message, django_request):
        """
        TODO: This isn't tested
        """
        prp = PollRequestProperties.from_poll_request_10(poll_service, poll_message)
        query_kwargs = prp.get_db_kwargs()
        content_blocks = cls.get_content(prp, query_kwargs)
        response = cls.create_poll_response(poll_service, prp, content_blocks)
        return response


class PollRequestHandler(BaseMessageHandler):
    """
    Built-in TAXII 1.1 and TAXII 1.0 Poll Request Handler
    """

    supported_request_messages = [tm10.PollRequest, tm11.PollRequest]
    version = "1"

    @staticmethod
    def handle_message(poll_service, poll_request, django_request):
        """
        Passes the request to either PollRequest10Handler or PollRequest11Handler
        """
        if isinstance(poll_request, tm10.PollRequest):
            return PollRequest10Handler.handle_message(poll_service, poll_request, django_request)
        elif isinstance(poll_request, tm11.PollRequest):
            return PollRequest11Handler.handle_message(poll_service, poll_request, django_request)
        else:
            raise StatusMessageException(poll_request.message_id,
                                         ST_FAILURE,
                                         "TAXII Message not supported by Message Handler.")
