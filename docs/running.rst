==================
Running OpenTAXII
==================

.. highlight:: sh

This guide describes how to run OpenTAXII in development and production mode.

Development mode
================

To run the server in development mode use CLI command shipped with OpenTAXII package::

   (venv) $ opentaxii-run-dev

This will start OpenTAXII in a development mode and bind it to ``localhost:9000``.


Production mode
===============

To run OpenTAXII in production it is recommended to use one of `standalone WSGI
containers <http://flask.pocoo.org/docs/0.10/deploying/wsgi-standalone/>`_ that work with Flask.

For example, to run OpenTAXII with `Gunicorn WSGI HTTP Server <http://gunicorn.org/>`_ execute::
    
    (venv) $ gunicorn opentaxii.http:app --bind localhost:9000

Common practice is to wrap gunicorn execution into `supervisord <http://supervisord.org>`_, to be able to monitor, start, and stop it easily.

Example supervisord configuration file:

.. code-block:: ini

    [program:opentaxii]

    command =
        /opt/intelworks/opentaxii-venv/bin/gunicorn opentaxii.http:app
            --workers 2
            --log-level info
            --log-file -
            --timeout 300
            --bind localhost:9000
    environment =
        OPENTAXII_CONFIG="/opt/intelworks/custom-opentaxii-configuration.yml"

    stdout_logfile = /var/log/opentaxii.log
    redirect_stderr = true
    autostart = true
    autorestart = true


Sending requests to services
============================

The easiest way to send requests to TAXII services is to use `Cabby library <http://github.com/Intelworks/cabby>`_ CLI tools::

    (venv) $ pip install cabby

If you are running OpenTAXII in default configuration and you created services using :doc:`provided examples <configuration>`, you should
be able to communicate with the services.

Assuming OpenTAXII is running on ``http://localhost:9000``, to get the list of advertised services, run::

    (venv) $ taxii-discovery --path http://localhost:9000/services/discovery-a

One of the configured services is a Collection Management Service. To get the collections list, run::

    (venv) $ taxii-collections --path http://localhost:9000/services/collection-management-a

See `Cabby documentation <http://cabby.readthedocs.org>`_ to get more examples of usage.


.. rubric:: Next steps

Continue to :doc:`Authentication <auth>` page to learn how OpenTAXII authentication process works.

.. vim: set spell spelllang=en:

