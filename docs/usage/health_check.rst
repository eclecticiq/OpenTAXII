============
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
