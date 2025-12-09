=============================
Running Development OpenTAXII
=============================

.. highlight:: sh

Here we describe how to run OpenTAXII in a *development*. Development mode
activates `Flask <http://flask.pocoo.org/>`_ debug mode, simplifies log messages
(for humans) and runs the server in one thread. While in production mode there
are no debug messages, proper json log messages and multithreaded if configured.

To run the server in development mode use the CLI command shipped with OpenTAXII package::

   (venv) $ opentaxii-run-dev

This will start OpenTAXII in a development mode and bind it to ``localhost:9000``.