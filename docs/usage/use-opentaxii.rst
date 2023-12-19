=============
Use OpenTAXII
=============

Sending requests to services
============================

The easiest way to send requests to TAXII services is to use `Cabby library <http://github.com/eclecticiq/cabby>`_ CLI tools::

    (venv) $ pip install cabby

If you are running OpenTAXII in default configuration and you created services using :doc:`provided examples <configuration>`, you should
be able to communicate with the services.

Assuming OpenTAXII is running on ``http://localhost:9000``, to get the list of advertised services, run::

    (venv) $ taxii-discovery --path http://localhost:9000/services/discovery-a

You should see the following output::

    2018-06-03 21:26:32,188 INFO: Sending Discovery_Request to http://localhost:9000/services/discovery-a
    2018-06-03 21:26:32,207 INFO: 7 services discovered
    === Service Instance ===
      Service Type: INBOX
      Service Version: urn:taxii.mitre.org:services:1.1
      Protocol Binding: urn:taxii.mitre.org:protocol:http:1.0
      Service Address: http://localhost:9000/services/inbox-a
      Message Binding: urn:taxii.mitre.org:message:xml:1.0
      Message Binding: urn:taxii.mitre.org:message:xml:1.1
      Inbox Service AC: []
      Available: True
      Message: Custom Inbox Service Description A

    === Service Instance ===
      Service Type: INBOX
      Service Version: urn:taxii.mitre.org:services:1.1
      Protocol Binding: urn:taxii.mitre.org:protocol:http:1.0
      Service Address: http://localhost:9000/services/inbox-b
      Message Binding: urn:taxii.mitre.org:message:xml:1.0
      Message Binding: urn:taxii.mitre.org:message:xml:1.1
      Inbox Service AC: ['urn:stix.mitre.org:xml:1.1.1', 'urn:custom.example.com:json:0.0.1']
      Available: True
      Message: Custom Inbox Service Description B

    === Service Instance ===
      Service Type: DISCOVERY
      Service Version: urn:taxii.mitre.org:services:1.1
      Protocol Binding: urn:taxii.mitre.org:protocol:http:1.0
      Service Address: http://localhost:9000/services/discovery-a
      Message Binding: urn:taxii.mitre.org:message:xml:1.0
      Message Binding: urn:taxii.mitre.org:message:xml:1.1
      Available: True
      Message: Custom Discovery Service description

    ..... snip .....

One of the configured services is a Collection Management Service. To get the collections list, run::

    (venv) $ taxii-collections --path http://localhost:9000/services/collection-management-a

You should see the following output::

    2018-06-03 21:30:03,315 INFO: Sending Collection_Information_Request to http://localhost:9000/services/collection-management-a
    === Data Collection Information ===
      Collection Name: collection-a
      Collection Type: DATA_SET
      Available: True
      Collection Description: None
      Supported Content: All
      === Polling Service Instance ===
        Poll Protocol: urn:taxii.mitre.org:protocol:http:1.0
        Poll Address: http://localhost:9000/services/poll-a
        Message Binding: urn:taxii.mitre.org:message:xml:1.0
        Message Binding: urn:taxii.mitre.org:message:xml:1.1
      === Subscription Service ===
        Protocol Binding: urn:taxii.mitre.org:protocol:http:1.0
        Address: http://localhost:9000/services/collection-management-a
        Message Binding: urn:taxii.mitre.org:message:xml:1.0
        Message Binding: urn:taxii.mitre.org:message:xml:1.1
      === Subscription Service ===
        Protocol Binding: urn:taxii.mitre.org:protocol:https:1.0
        Address: https://localhost:9000/services/collection-management-a
        Message Binding: urn:taxii.mitre.org:message:xml:1.0
        Message Binding: urn:taxii.mitre.org:message:xml:1.1
      === Receiving Inbox Service ===
        Protocol Binding: urn:taxii.mitre.org:protocol:http:1.0
        Address: http://localhost:9000/services/inbox-a
        Message Binding: urn:taxii.mitre.org:message:xml:1.0
        Message Binding: urn:taxii.mitre.org:message:xml:1.1
        Supported Contents: All
    ==================================


    === Data Collection Information ===
      Collection Name: collection-b
      Collection Type: DATA_FEED
      Available: True
      Collection Description: None
      Supported Content:   urn:stix.mitre.org:xml:1.1.1
      === Polling Service Instance ===
        Poll Protocol: urn:taxii.mitre.org:protocol:http:1.0
        Poll Address: http://localhost:9000/services/poll-a
        Message Binding: urn:taxii.mitre.org:message:xml:1.0
        Message Binding: urn:taxii.mitre.org:message:xml:1.1
      === Subscription Service ===
        Protocol Binding: urn:taxii.mitre.org:protocol:http:1.0
        Address: http://localhost:9000/services/collection-management-a
        Message Binding: urn:taxii.mitre.org:message:xml:1.0
        Message Binding: urn:taxii.mitre.org:message:xml:1.1
      === Subscription Service ===
        Protocol Binding: urn:taxii.mitre.org:protocol:https:1.0
        Address: https://localhost:9000/services/collection-management-a
        Message Binding: urn:taxii.mitre.org:message:xml:1.0
        Message Binding: urn:taxii.mitre.org:message:xml:1.1
      === Receiving Inbox Service ===
        Protocol Binding: urn:taxii.mitre.org:protocol:http:1.0
        Address: http://localhost:9000/services/inbox-a
        Message Binding: urn:taxii.mitre.org:message:xml:1.0
        Message Binding: urn:taxii.mitre.org:message:xml:1.1
        Supported Contents: All
      === Receiving Inbox Service ===
        Protocol Binding: urn:taxii.mitre.org:protocol:http:1.0
        Address: http://localhost:9000/services/inbox-b
        Message Binding: urn:taxii.mitre.org:message:xml:1.0
        Message Binding: urn:taxii.mitre.org:message:xml:1.1
        Supported Content: urn:stix.mitre.org:xml:1.1.1
        Supported Content: urn:custom.example.com:json:0.0.1
    ==================================

    .... snip .....


See `Cabby documentation <http://cabby.readthedocs.org>`_ for more examples.

Health check
============

OpenTAXII has an endpoint that can be used to check health of the service::

    $ curl http://localhost:9000/management/health
    {
      "alive": true
    }

.. rubric:: Next steps

Continue to :doc:`Authentication <../usage/auth>` page to learn how OpenTAXII authentication process works.

.. vim: set spell spelllang=en:
