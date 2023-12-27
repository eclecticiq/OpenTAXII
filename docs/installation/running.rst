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

Continue to :doc:`Manage OpenTAXII <../usage/manage>` page to learn how to OpenTAXII create services, collections, and accounts.

.. vim: set spell spelllang=en:

