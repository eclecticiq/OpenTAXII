=================================
TAXII 2: API Root and collections
=================================

API Root and collections can be created with CLI commands or with custom code
talking to a specific Persistent API implementation/backend.

CLI commands
============

.. code-block:: shell

    opentaxii-add-api-root --title default --description "The default API root" --default

    opentaxii-add-collection --rootid <root-uuid> --title "A collection" --public
