# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

from ..exceptions import StatusMessageException

import libtaxii.taxii_default_query as tdq
from libtaxii.constants import *

from lxml import etree

# Define stub predicates for each relationship. Stub predicates have a placeholder for the operand and value
EQ_CS = '[%s = \'%s\']'
EQ_CI ='[translate(%s, \'ABCDEFGHIJKLMNOPQRSTUVWXYZ\', \'abcdefghijklmnopqrstuvwxyz\') = \'%s\']'
EQ_N = '[%s = \'%s\']'
NEQ_CS = '[%s != \'%s\']'
NEQ_CI = '[translate(%s, \'ABCDEFGHIJKLMNOPQRSTUVWXYZ\', \'abcdefghijklmnopqrstuvwxyz\') != \'%s\']'
NEQ_N = '[%s != \'%s\']'
GT = '[%s > \'%s\']'
GTE = '[%s >= \'%s\']'
LT = '[%s < \'%s\']'
LTE = '[%s <= \'%s\']'
EX = ''
DNE = '????????????????????????????'
BEGIN_CS = '[contains(%s, \'%s\')]'
BEGIN_CI = '[starts-with(translate(%s, \'ABCDEFGHIJKLMNOPQRSTUVWXYZ\', \'abcdefghijklmnopqrstuvwxyz\'), \'%s\')]'
CONTAINS_CS = '[contains(%s, \'%s\')]'
CONTAINS_CI = '[contains(translate(%s, \'ABCDEFGHIJKLMNOPQRSTUVWXYZ\', \'abcdefghijklmnopqrstuvwxyz\'), \'%s\')]'
ENDS_CS = '[substring(%s, string-length(%s) - string-length(\'%s\') + 1) = \'%s\']'
ENDS_CI = '[substring(translate(%s, \'ABCDEFGHIJKLMNOPQRSTUVWXYZ\', \'abcdefghijklmnopqrstuvwxyz\'), string-length(%s) - string-length(\'%s\') + 1) = \'%s\']'


class XPathBuilder(object):
    """
    The XPathBuilder object is a helper object that stores an intermediate form of
    XPath (a list of xpath parts and a namespace map) and can build that intermediate form
    into a full xpath when given a relationship (e.g., equals) and TAXII Default Query parameters.

    The object is instantiated with the __init__ method, and full XPaths are created by using the build() method.
    """
    def __init__(self, xpath_parts, nsmap):
        """
        Creates an XPathBuilder object.

        :param xpath_parts: A list of xpath parts. E.g., ['stix:STIX_Package','stix:STIX_Header','stix:Title']
        :param nsmap: A dict containing an nsmap that can be used in
        """

        self.xpath_parts = xpath_parts
        self.nsmap = nsmap

    def build(self, relationship, params):
        """
        Uses self.xpath_parts to build up an XPath Expression - e.g., turning ['stix:STIX_Package','stix:STIX_Header',
        'stix:Title'] into /stix:STIX_Package/stix:STIX_Header/stix:Title. Then uses the specified relationship
        and parameters to append an appropriate predicate (e.g., [text() = 'value']. All combined, this function
        returns something like "/stix:STIX_Package/stix:STIX_Header/stix:Title[text() = 'value']"


        :param relationship: A string containing a relationship (e.g., 'equals')
        :param params: A dict containing TAXII Default Query parameters

        :return: A string containing an XPath build based on self.xpath_arts, relationship, and parameters.
        """

        # Create the XPath Expression
        expr = '/'.join(self.xpath_parts)

        # If the last part of the XPath Expression is an attribute, the operand (the left hand side of the predicate)
        # is '.'. If the last part of the XPath Expression is an element, the operand is 'text()'
        last_part = self.xpath_parts[-1]
        if last_part.startswith('@'):
            operand = '.'
        else:
            operand = 'text()'

        # Get the value of the Test, if it exists
        v = params.get(P_VALUE, None)

        # Go through each relationship/parameter combination and append the appropriate predicate to
        # The XPath Expression. The predicate is formed (in most cases) by injecting the operand and value
        # into a predefined predicate stub.

        # Relationship equals
        if relationship == R_EQUALS and params[P_MATCH_TYPE] == 'case_sensitive_string':
            expr += EQ_CS % (operand, v)
        elif relationship == R_EQUALS and params[P_MATCH_TYPE] == 'case_insensitive_string':
            expr += EQ_CI % (operand, v.lower())
        elif relationship == R_EQUALS and params[P_MATCH_TYPE] == 'number':
            expr += EQ_N % (operand, v)

        # Take a breather before jumping into the next relationship, not equals

        elif relationship == R_NOT_EQUALS and params[P_MATCH_TYPE] == 'case_sensitive_string':
            expr += NEQ_CS % (operand, v)
        elif relationship == R_NOT_EQUALS and params[P_MATCH_TYPE] == 'case_insensitive_string':
            expr += NEQ_CI % (operand, v.lower())
        elif relationship == R_NOT_EQUALS and params[P_MATCH_TYPE] == 'number':
            expr += NEQ_N % (operand, v)

        # Next set of relationships, gt, lt, gte, lte

        elif relationship == R_GREATER_THAN:
            expr += GT % (operand, v)
        elif relationship == R_GREATER_THAN_OR_EQUAL:
            expr += GTE % (operand, v)
        elif relationship == R_LESS_THAN:
            expr += LT % (operand, v)
        elif relationship == R_LESS_THAN_OR_EQUAL:
            expr += LTE % (operand, v)

        # Next set of relationships, Exists/DoesNotExist

        elif relationship == R_DOES_NOT_EXIST:
            raise ValueError('Need to code this!')
            # expr += 'not(' + xpath_string + ')'
        elif relationship == R_EXISTS:
            raise ValueError('Need to code this!')
            # expr + # nothing necessary

        # Next, begins with
        elif relationship == R_BEGINS_WITH and params[P_CASE_SENSITIVE] == 'false':
            expr += BEGIN_CS % (operand, v.lower())
        elif relationship == R_BEGINS_WITH and params[P_CASE_SENSITIVE] == 'true':
            expr += BEGIN_CI % (operand, v)

        # Next, contains

        elif relationship == R_CONTAINS and params[P_CASE_SENSITIVE] == 'false':
            expr += CONTAINS_CS % (operand, v.lower())
        elif relationship == R_CONTAINS and params[P_CASE_SENSITIVE] == 'true':
            expr += CONTAINS_CS % (operand, v)

        # Lastly, ends with

        elif relationship == R_ENDS_WITH and params[P_CASE_SENSITIVE] == 'false':
            expr += ENDS_CI % (operand, operand, v, v.lower())
        elif relationship == R_ENDS_WITH and params[P_CASE_SENSITIVE] == 'true':
            expr += ENDS_CS % (operand, operand, v, v)
        else:
            raise ValueError("Unknown values: %s, %s" % (relationship, params))

        return expr


class BaseQueryHandler(object):

    """
    QueryHandler is the base class for TAXII Query
    Handlers.

    Child classes MUST specify a value for QueryHandler.supported_targeting_expression,
    and QueryHandler.supported_capability_modules
    and MUST implement the execute_query function.

    e.g.,::

        import libtaxii.messages_11 as tm11
        import libtaxii.taxii_default_query as tdq
        from libtaxii.constants import *

        QueryHandlerChild(QueryHandler):
            supported_targeting_expression = CB_STIX_XML_111
            supported_capability_modules = [tdq.CM_CORE]

            @classmethod
            def execute_query(cls, content_block_list, query):
                matching_content_blocks = []
                for cb in content_block_list:
                    matches = # code to execute the query
                    if matches:
                    matching_content_blocks.append(cb)
                return matching_content_blocks

    Optionally,register the QueryHandler child:
    import taxii_services.management as m
    m.register_query_handler(QueryHandlerChild, name='QueryHandlerChild')
    """

    supported_tevs = None
    supported_cms = None

    def __init__(self):
        if self.supported_tevs is None:
            raise NotImplementedError("The subclass did not specify a value for supported_tevs")

        if self.supported_cms is None:
            raise NotImplementedError("The subclass did not specify a value for supported_cms")

    @classmethod
    def is_target_supported(cls, target):
        raise NotImplementedError()

    @classmethod
    def get_supported_cms(cls):
        return cls.supported_cms

    @classmethod
    def get_supported_tevs(cls):
        return cls.supported_tevs

    @classmethod
    def update_db_kwargs(cls, poll_request_properties, db_kwargs):
        """
        This is a hook used by PollRequest11Handler that allows a query handler to modify the params_dict
        before being passed into the database.

        The default behavior of this method is to do nothing.

        Arguments:
            poll_request_properties - a PollRequestProperties object
            db_kwargs - a dict containing the results of PollRequestProperties.get_db_kwargs()
        """
        return db_kwargs

    @classmethod
    def filter_content(cls, poll_request_properties, content_blocks):
        """
        This is a hook used by PollRequest11Handler that allows a query handler to modify the database result set
        after being retrieved from the database and before it is returned to the
        requester. Default behavior is to do nothing.

        :param poll_request_properties: A util.PollRequestProperties object
        :param content_blocks: A list of ContentBlock objects
        :return: a list of ContentBlock objects
        """
        return content_blocks


class BaseXmlQueryHandler(BaseQueryHandler):
    """
    Extends the QueryHandler for general XML / XPath
    processing. This class still needs to be extended
    to support specific XML formats (e.g., specific
    versions of STIX).


    There is a generate_xml_query_extension.py script
    to help with extending this class

    Note that correctly specifying the mapping_dict is
    a critical aspect of extending this class. The mapping_dict
    should adhere to the following format::

        { 'root_context':
            {'children':
                '<xml_root_element_name>':
                {
                   'has_text': True/False,
                   'namespace': '<namespace>',
                   'prefix': 'prefix', # aka namespace alias
                   'children':
                   {
                      '@<attribute_child>': { # can have 0-n of these
                        'has_text': True, # attributes can always have text
                        'namespace': <namespace> or None,
                        'prefix': <prefix> or None,
                        'children': {} #Attributes can't have children
                      },
                      '<element_child>': { # Can have 0-n of these
                        'has_text': True or False, #Depending on whether the element value can hold text
                        'namespace': <namespace> or None,
                        'prefix': <prefix> or None,
                        'children': { ... } # Any number of @<attribute_child> or <element_child> instances
                      },
                   }
                }
            }
        }
    """

    supported_capability_modules = [tdq.CM_CORE]
    version = "1"

    mapping_dict = None

    @classmethod
    def is_target_supported(cls, target):
        """
        Overrides the parent class' method.

        If the scope can be turned into an XPath, the scope is supported.

        Note: This function may change in the future (specifically, the returning
        a tuple part)
        """

        try:
            cls.target_to_xpath_builders(None, target)
        except ValueError as e:
            return SupportInfo(False, traceback.format_exc(e))

        return SupportInfo(True, None)

    @classmethod
    def evaluate_criteria(cls, prp, content_etree, criteria):
        """
        Evaluates the criteria in a query. Note that criteria can have
        child criteria (which will cause recursion) and child criterion.

        Arguments:
            content_etree - an lxml etree to evaluate
            criteria - the criteria to evaluate against the etree

        Returns:
            True or False, indicating whether the content_etree
            matches the criteria

        """

        for child_criteria in criteria.criteria:
            value = cls.evaluate_criteria(prp, content_etree, child_criteria)
            if value is True and criteria.operator == tdq.OP_OR:
                return True
            elif value is False and criteria.operator == tdq.OP_AND:
                return False
            else:  # Don't know anything for sure yet
                pass

        for criterion in criteria.criterion:
            value = cls.evaluate_criterion(prp, content_etree, criterion)
            # TODO: Is there a way to keep this DRY?
            if value is True and criteria.operator == tdq.OP_OR:
                return True
            elif value is False and criteria.operator == tdq.OP_AND:
                return False
            else:  # Don't know anything for sure yet
                pass

        return criteria.operator == tdq.OP_AND

    @classmethod
    def evaluate_criterion(cls, prp, content_etree, criterion):
        """
        Evaluates the criterion in a query by turning the Criterion into an XPath and
        evaluating it against the content_etree

        Arguments:
            content_etree - an lxml etree to evaluate
            criterion - the criterion to evaluate against the etree

        Returns:
            True or False, indicating whether the content_etree
            matches the criterion
        """

        xpath, nsmap = cls.get_xpath(prp, criterion)
        # print xpath
        matches = content_etree.xpath(xpath, namespaces=nsmap)
        # XPath results can be a boolean (True, False) or
        # a NodeSet
        if matches in (True, False):  # The result is boolean, take it literally
            result = matches
        else:  # The result is a NodeSet. The Criterion is True iff there are >0 resulting nodes
            result = len(matches) > 0

        if criterion.negate:
            return not result

        return result


    @classmethod
    def get_xpath(cls, prp, criterion):
        """
        Given a tdq.Criterion, return an XPath that is equivalen

        :param prp: PollRequestProperties
        :param criterion: tdq.Criterion
        :return: The full XPath to evaluate that maps to the tdq.Criterion
        """
        xpath_builders, nsmap = cls.target_to_xpath_builders(prp, criterion.target)
        xpaths = [xp.build(criterion.test.relationship, criterion.test.parameters) for xp in xpath_builders]
        xpath = " or ".join(xpaths)
        return xpath, nsmap


    @classmethod
    def target_to_xpath_builders(cls, prp, target):
        """
        Turns a Targeting Expression into an XPath stub.

        :param prp: PollRequestProperties object
        :param target: A string Targeting Expression
        :return: A list of 1-2 XPathBuilder objects, nsmap (dict)
        """

        # Determine the class of Targeting Expression and sub out to the relevant subcall

        target_tokens = target.split('/')

        # Test for Naked/Trailing (N/T) Wildcard
        if target.endswith('*'):
            xpath_builders, nsmap = cls.get_nt_wildcard_xpath_builders(prp, target_tokens)
        # Test for Leading/Middle (L/M) Wildcard
        elif '*' in target:
            xpath_builders, nsmap = cls.get_lm_wildcard_xpath_builders(prp, target_tokens)
        else:  # Assume no wildcards
            xpath_builders, nsmap = cls.get_no_wildcard_xpath_builders(prp, target_tokens)

        return xpath_builders, nsmap

    @classmethod
    def get_nt_wildcard_xpath_builders(cls, prp, target_tokens):
        """
        For the Naked/Trailing Wildcard class of Targeting Expressions, which are all Targeting Expressions
        that have a wildcard that is "Naked" (e.g., all by itself) or Trailing (e.g., at the end of the Targeting
        Expression), create an XPathBuilder object.

        :param prp: PollRequestProperties
        :param target_tokens: A tokenized list of Targeting Expressions

        :return: A list of XPathBuilder objects
        """
        xpath_parts = ['']
        context = cls.mapping_dict['root_context']  # Start at the root of the mapping_dict
        nsmap = {}

        wc_type = 'unknown'

        for token in target_tokens:
            if token == '*':
                wc_type = 'single'
                break
            elif token == '**':
                wc_type = 'multi'
                break

            context = context['children'].get(token, None)
            if context is None:
                raise ValueError('Unknown token: %s' % token)
            namespace = context.get('namespace', None)
            if namespace is not None:
                prefix = context['prefix']
                xpath_parts.append(prefix + ':' + token)
                nsmap[prefix] = namespace
            else:
                xpath_parts.append(token)

        if wc_type == 'multi':  # Insert an empty part to make the double slash (//) appear in the build expression
            xpath_parts.append('')

        # Create the XPath parts for the element expression
        elt_xpath_parts = list(xpath_parts)  # Clone xpath_parts
        elt_xpath_parts.append('*')

        # Create the XPath parts for the attribute expression
        attr_xpath_parts = list(xpath_parts)  # Clone xpath_parts
        attr_xpath_parts.append('@*')

        elt_builder = XPathBuilder(elt_xpath_parts, nsmap)
        attr_builder = XPathBuilder(attr_xpath_parts, nsmap)

        return [elt_builder, attr_builder], nsmap

    @classmethod
    def single_field_lookahead(cls, future_token, context):
        """
        Looks in the context's grandchildren for future_token.

        Looking for context/*/future_token
        * is 'children'
        future_token is a grandchild

        :param future_token: The token to look for
        :param context: The context to look in
        :return: The context whose children contains future_token
        """

        ctx_children = context.get('children', None)
        if ctx_children is None:
            raise ValueError('Context has no children!')

        for k, v in ctx_children.iteritems():
            if future_token in v.get('children', {}):
                return v  # If future_token is found, return the context that contains future_token

        raise ValueError('Lookahead failed for %s' % future_token)

    @classmethod
    def multi_field_lookahead(cls, future_token, context, max_depth=1000, depth=0):
        """
        The look_ahead does a depth first search on the context
        looking for future_token, and stops looking when depth = max_depth.

        There is a possible error in logic where future_token exists in multiple search trees.

        This is used for the multi-field wildcard

        :param future_token: The token to look for
        :param context: The current context
        :param max_depth: The maximum depth to look, defaults to 1000
        :return: The future token's context
        """

        # depth = current context
        # depth + 1 = current context's children
        # if depth +1 is too far, can't look at the children and have to return None
        if depth + 1 > max_depth:
            # print 'max_depth of %s exceeded. Returning None' % max_depth
            return None

        ctx_children = context.get('children', {})
        new_ctx = ctx_children.get(future_token, None)

        # If future_token is found, return it's parent (so that context['children']['future_token'] works)
        if new_ctx is not None:
            # print 'Found future_token, returning', context
            return context

        # No children, can't look ahead any further
        if len(ctx_children) == 0:
            # print 'len(ctx_children) == 0, returning None'
            return None

        # As long as there is depth, recursively search each child
        for k, v in ctx_children.iteritems():
            # print 'recursing for ', k
            x = cls.multi_field_lookahead(future_token, v, max_depth=max_depth, depth=depth+1)
            if x is not None:
                # print 'recurse for %s was not None, returning' % k
                return x
            # print 'recurse for %s was None, continuing search' % k

        # print 'end of function - returning None'
        return None  # Nothing has been found

    @classmethod
    def get_lm_wildcard_xpath_builders(cls, prp, target_tokens):
        xpath_parts = ['']
        context = cls.mapping_dict['root_context']  # Start at the root of the mapping_dict
        nsmap = {}
        max_ = len(target_tokens)
        i = 0
        while i < max_:
            token = target_tokens[i]

            # There are three ways to advance the context
            if token == '*':
                future_token = target_tokens[i + 1]
                context = cls.single_field_lookahead(future_token, context)
                xpath_parts.append(token)

            elif token == '**':

                future_token = target_tokens[i + 1]
                context = cls.multi_field_lookahead(future_token, context)
                # print context
                if context is None:
                    raise ValueError("Lookahead failed for %s" % future_token)

                if len(xpath_parts) == 1:  # This is a leading wildcard, replace the 0th element
                    xpath_parts[0] = '/'
                else:  # This is a middle wildcard
                    xpath_parts.append('')  # Will cause two slashes to get joined
            else:
                context = context['children'].get(token, None)
                if context is None:
                    raise ValueError('Unknown token: %s' % token)
                namespace = context.get('namespace', None)
                if namespace is not None:
                    prefix = context['prefix']
                    xpath_parts.append(prefix + ':' + token)
                    nsmap[prefix] = namespace
                else:
                    xpath_parts.append(token)
            i += 1

        # print xpath_parts
        xpath_builders = [XPathBuilder(xpath_parts, nsmap)]
        return xpath_builders, nsmap

    @classmethod
    def get_no_wildcard_xpath_builders(cls, prp, target_tokens):
        xpath_parts = ['']
        context = cls.mapping_dict['root_context']  # Start at the root of the mapping_dict
        nsmap = {}

        for token in target_tokens:
            context = context['children'].get(token, None)
            if context is None:
                raise ValueError('Unknown token: %s' % token)
            namespace = context.get('namespace', None)
            if namespace is not None:
                prefix = context['prefix']
                xpath_parts.append(prefix + ':' + token)
                nsmap[prefix] = namespace
            else:
                xpath_parts.append(token)

        xpath_builders = [XPathBuilder(xpath_parts, nsmap)]
        return xpath_builders, nsmap

    @classmethod
    def filter_content(cls, prp, content_blocks):
        """
        Turns the prp.query into an XPath, runs the XPath against each
        item in `content_blocks`, and returns the items in `content_blocks`
        that match the XPath.

        :param prp: A PollRequestParameters object representing the Poll Request
        :param content_blocks: A list of models.ContentBlock objects to filter
        :return: A list of models.ContentBlock objects matching the query
        """
        if prp.query.targeting_expression_id not in cls.get_supported_tevs():
            raise StatusMessageException(prp.message_id,
                                         ST_UNSUPPORTED_TARGETING_EXPRESSION_ID,
                                         status_detail={SD_TARGETING_EXPRESSION_ID: cls.get_supported_tevs()})

        result_list = []
        for content_block in content_blocks:
            etree_content = etree.XML(content_block.content)
            if cls.evaluate_criteria(prp, etree_content, prp.query.criteria):
                result_list.append(content_block)

        return result_list
