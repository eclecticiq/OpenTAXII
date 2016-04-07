==================
Running OpenTAXII
==================

.. highlight:: sh

Here we describe how to run OpenTAXII in a *development* or *production* mode. Development mode activates `Flask <http://flask.pocoo.org/>`_ debug mode, simplifies log messages (for humans) and runs the server in one thread. While in production mode there are no debug messages, proper json log messages and multithreaded if configured.

Development mode
================

To run the server in development mode use the CLI command shipped with OpenTAXII package::

   (venv) $ opentaxii-run-dev

This will start OpenTAXII in a development mode and bind it to ``localhost:9000``.


Production mode
===============

To run OpenTAXII in production it is recommended to use one of the `standalone WSGI
containers <http://flask.pocoo.org/docs/0.10/deploying/wsgi-standalone/>`_ that work with Flask. In this example we use `Gunicorn WSGI HTTP Server <http://gunicorn.org/>`_.

.. note::
	Run `pip install gunicorn` to install gunicorn. Yes it's that simple.

To run OpenTAXII with Gunicorn execute::
    
    (venv) $ gunicorn opentaxii.http:app --bind localhost:9000

Common practice is to wrap gunicorn execution into `supervisord <http://supervisord.org>`_, to be able to monitor, start, and stop it easily.

Example supervisord configuration file:

.. code-block:: ini

    [program:opentaxii]

    command =
        /opt/eclecticiq/opentaxii-venv/bin/gunicorn opentaxii.http:app
            --workers 2
            --log-level info
            --log-file -
            --timeout 300
            --bind localhost:9000
    environment =
        OPENTAXII_CONFIG="/opt/eclecticiq/custom-opentaxii-configuration.yml"

    stdout_logfile = /var/log/opentaxii.log
    redirect_stderr = true
    autostart = true
    autorestart = true


Sending requests to services
============================

The easiest way to send requests to TAXII services is to use `Cabby library <http://github.com/eclecticiq/cabby>`_ CLI tools::

    (venv) $ pip install cabby

If you are running OpenTAXII in default configuration and you created services using :doc:`provided examples <configuration>`, you should
be able to communicate with the services.

Assuming OpenTAXII is running on ``http://localhost:9000``, to get the list of advertised services, run::

    (venv) $ taxii-discovery --path http://localhost:9000/services/discovery-a
    
You should see the following output::

	2015-04-03 13:51:35,726 INFO: Sending Discovery_Request to http://localhost:9000/services/discovery-a
	{"level": "info", "timestamp": "2015-04-03T11:51:35.788228Z", "event": "Processing message", "message_version": "urn:taxii.mitre.org:message:xml:1.1", "service_id": "discovery_a", "logger": "opentaxii.taxii.services.discovery.DiscoveryService", "message_type": "Discovery_Request", "message_id": "8b7d6fb8-7c74-46d5-a74f-71a9662f3cd9"}
	2015-04-03 13:51:35,793 INFO: Response received for Discovery_Request from http://localhost:9000/services/discovery-a
	2015-04-03 13:51:35,793 INFO: 7 services discovered
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

	2015-04-03 13:53:50,516 INFO: Sending Collection_Information_Request to http://localhost:9000/services/collection-management-a
	{"level": "info", "timestamp": "2015-04-03T11:53:50.526007Z", "event": "Processing message", "message_version": "urn:taxii.mitre.org:message:xml:1.1", "service_id": "collection_management_a", "logger": "opentaxii.taxii.services.collection_management.CollectionManagementService", "message_type": "Collection_Information_Request", "message_id": "cf1fed62-51bb-470c-a4f1-52b512df7f10"}
	2015-04-03 13:53:50,599 INFO: Response received for Collection_Information_Request from http://localhost:9000/services/collection-management-a
	=== Data Collection Information ===
	  Collection Name: collection-A
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
	  Collection Name: collection-B
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

Continue to :doc:`Authentication <auth>` page to learn how OpenTAXII authentication process works.

.. vim: set spell spelllang=en:

