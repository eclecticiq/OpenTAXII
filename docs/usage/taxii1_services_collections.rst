=================================
TAXII 1: Services and Collections
=================================

Services and Collections can be created with CLI commands
``opentaxii-sync-data`` or with custom code talking to a specific Persistence API
implementation/backend.

..  Note::
    The services and collections created with CLI command ``opentaxii-sync-data`` are only available with TAXII 1.

Step 1
------
Create YAML file with collections/services/accounts configuration. See provided example from `OpenTAXII git repo <https://github.com/eclecticiq/OpenTAXII>`_ — file :github-file:`examples/data-configuration.yml <examples/data-configuration.yml>` that contains:

Services:
    * 2 Inbox Services (with ids ``inbox_a`` and ``inbox_b``),
    * 1 Discovery Service (with id ``discovery_a``),
    * 1 Collection Management Service (with id ``collection_management_a``),
    * 1 Poll Service (with id ``poll_a``).

.. note::
    Services have relative path in the address field, which means OpenTAXII will prepend it with domain configured in server configuration file (``localhost:9000`` in Default configuration).

Collections:
    * ``collection-a`` that has type ``DATA_SET``, accepts all content types and is attached to services
      ``inbox_a``, ``collection_management_a``, and ``poll_a``.
    * ``collection-b`` that accepts only content types specified in field ``content_bindings`` and is attached to services ``inbox_a``, ``inbox_b``, ``collection_management_a`` and ``poll_a``.
    * ``collection-c`` that accepts not only STIX v1.1.1 content type but also custom content type ``urn:custom.bindings.com:json:0.0.1``. It is attached to services ``inbox_a``, ``collection_management_a`` and ``poll_a``.
    * ``col-not-available`` that is marked as not available, even though it is attached to ``inbox_b`` and ``collection_management_a``.

Accounts:
    * account with username ``test`` and password ``test``, with ability to modify collection ``collection-a``, read ``collection-b`` and ``coll-stix-and-custom``, and unknown permission ``some`` for non-existing collection ``collection-xyz``. Incorrect settings will be ignored during sync.
    * account with username ``admin`` and password ``admin`` that has admin permissions because ``is_admin`` is set to ``yes``.

.. note::
	Without an account you can't access services with ``authentication_required`` enabled.

Step 2
------
Use ``opentaxii-sync-data`` command to synchronize data configuration in provided file and in DB.

Usage help::

    (venv) $ opentaxii-sync-data --help
    usage: opentaxii-sync-data [-h] [-f] config

    Create services/collections/accounts

    positional arguments:
      config              YAML file with data configuration

    optional arguments:
      -h, --help          show this help message and exit
      -f, --force-delete  force deletion of collections and their content blocks
                          if collection is not defined in configuration file
                          (default: False)

To sync data run::

  (venv) $ opentaxii-sync-data examples/data-configuration.yml

.. note::
	To drop the databases, just delete sqlite3 files ``/tmp/data.db``, ``/tmp/auth.db`` and restart OpenTAXII server.

Now OpenTAXII has services, collections and accounts configured and can function as a TAXII server.
Check :doc:`Use OpenTAXII <../installation/running>` to see how to use it.