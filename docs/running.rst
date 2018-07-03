=================
Running OpenTAXII
=================

.. highlight:: sh

Here we describe how to run OpenTAXII in a *development* or *production* mode. Development mode activates `Flask <http://flask.pocoo.org/>`_ debug mode, simplifies log messages (for humans) and runs the server in one thread. While in production mode there are no debug messages, proper json log messages and multithreaded if configured.

Development mode
================

To run the server in development mode use the CLI command shipped with OpenTAXII package::

   (venv) $ opentaxii-run-dev

This will start OpenTAXII in a development mode and bind it to ``localhost:9000``.


Production mode
===============

To run OpenTAXII in production it is recommended to use `standalone WSGI
container
<http://flask.pocoo.org/docs/1.0/tutorial/deploy/#run-with-a-production-server>`_
that works with Flask. In this example we use `Gunicorn WSGI HTTP Server
<http://gunicorn.org/>`_. For complete logging configuration we recommend
Gunicorn 19.8 and above.

.. note::
	Run ``pip install gunicorn`` to install gunicorn. Yes, it's that simple.

To run OpenTAXII with Gunicorn execute::

    (venv) $ gunicorn opentaxii.http:app \
      --bind localhost:9000 --config python:opentaxii.http

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
            --config python:opentaxii.http
    environment =
        OPENTAXII_CONFIG="/opt/eclecticiq/custom-opentaxii-configuration.yml"

    stdout_logfile = /var/log/opentaxii.log
    redirect_stderr = true
    autostart = true
    autorestart = true


Using SSL/TLS
=============

If you want to run OpenTAXII with SSL, you need to use a web server like `Nginx <https://nginx.org/en/>`_, that provides SSL/TLS layer. You can find details on how to run Nginx with SSL `here <https://nginx.org/en/docs/http/configuring_https_servers.html>`_.

Make sure you configure your TAXII services in OpenTAXII with proper protocol bindings:

    * use ``urn:taxii.mitre.org:protocol:https:1.0`` if you're planning on serving data via HTTPS.
    * use ``urn:taxii.mitre.org:protocol:http:1.0`` if the server is going to support unsecure HTTP as well.

You can use multiple protocol bindings per service. That would tell OpenTAXII you want to advertise services over both HTTPs and HTTP. TAXII services create external URLs according to their protocol bindings, using ``http://`` or ``https://`` schemas.


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

Continue to :doc:`Authentication <auth>` page to learn how OpenTAXII authentication process works.

.. vim: set spell spelllang=en:

