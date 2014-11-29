#!/usr/bin/env python
# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

from libtaxii.scripts import TaxiiScript, InboxClient10Script
import libtaxii.messages_11 as tm11
import libtaxii.messages_10 as tm10
import libtaxii as t
import StringIO


class InboxClient11(TaxiiScript):
    parser_description = 'TAXII 1.1 Inbox Client'
    path = '/services/inbox/'

    def get_arg_parser(self, *args, **kwargs):
        parser = super(InboxClient11, self).get_arg_parser(*args, **kwargs)
        parser.add_argument("--content-binding", dest="content_binding", default=t.CB_STIX_XML_111,
                help="Content binding of the Content Block to send. Defaults to %s" % t.CB_STIX_XML_111)
        parser.add_argument("--subtype", dest="subtype", default=None, help="The subtype of the Content Binding. Default: None")
        parser.add_argument("--content-file", dest="content_file", help="Content of the Content Block to send")
        parser.add_argument("--dcn", dest="dcn", default=None,
                help="The Destination Collection Name for this Inbox Message. Default: None. This script only supports one Destination Collection Name")
        return parser

    def create_request_message(self, args):

        with open(args.content_file, 'r') as payload_file:
            content_block = tm11.ContentBlock(tm11.ContentBinding(args.content_binding), payload_file.read())

        if args.subtype:
            content_block.content_binding.subtype_ids.append(args.subtype)

        inbox_message = tm11.InboxMessage(message_id=tm11.generate_message_id(), content_blocks=[content_block, content_block])
        if args.dcn:
            inbox_message.destination_collection_names.append(args.dcn)

        return inbox_message


class InboxClient10(InboxClient10Script):
    parser_description = 'TAXII 1.0 Inbox Client'
    path = '/services/inbox/'

    def get_arg_parser(self, *args, **kwargs):
        parser = super(InboxClient10, self).get_arg_parser(*args, **kwargs)
        parser.add_argument("--content-binding", dest="content_binding", default=t.CB_STIX_XML_111,
                help="Content binding of the Content Block to send. Defaults to %s" % t.CB_STIX_XML_111)
        parser.add_argument("--content-file", dest="content_file", help="Content of the Content Block to send")
        return parser

    def create_request_message(self, args):

        with open(args.content_file, 'r') as payload_file:
            content_block = tm10.ContentBlock(args.content_binding, payload_file.read())

        inbox_message = tm10.InboxMessage(message_id=tm10.generate_message_id(), content_blocks=[content_block])
        return inbox_message



if __name__ == "__main__":

    InboxClient11()()
    #InboxClient10()()
