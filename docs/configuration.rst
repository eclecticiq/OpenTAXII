=============
Configuration
=============

.. highlight:: sh

OpenTAXII can be configured using YAML configuration files.


Default configuration
=====================

OpenTAXII has default :github-file:`configuration file <opentaxii/defaults.yml>` built in.

By default:
    - Provided Persistence API and Authentication API implementations are for SQL DB backends and use sqlite3 backend.
    - The sqlite3 database files will be automatically created in ``/tmp/data.db`` and ``/tmp/auth.db``.
    - Services, collections and accounts are not configured automatically. This requires a manual operation (see below).
    - No signal hooks are attached.


Default configuration file looks like this:

.. code-block:: yaml

    ---
    domain: "localhost:9000"

    support_basic_auth: yes
    save_raw_inbox_messages: yes
    xml_parser_supports_huge_tree: yes
    count_blocks_in_poll_responses: no
    return_server_error_details: no

    persistence_api:
      class: opentaxii.persistence.sqldb.SQLDatabaseAPI
      parameters:
        db_connection: sqlite:////tmp/data.db
        create_tables: yes

    auth_api:
      class: opentaxii.auth.sqldb.SQLDatabaseAPI
      parameters:
        db_connection: sqlite:////tmp/auth.db
        create_tables: yes
        secret: SECRET-STRING-NEEDS-TO-BE-CHANGED

    logging:
      opentaxii: info
      root: info

    hooks: 
    
.. note::
  OpenTAXII uses a SQLite Database by default wich is intended only when running OpenTAXII in a development environment. Please use different SQL DB backend for running in a production environment.

An example of custom configuration that allows OpenTAXII to connect to production-ready PostgreSQL database:

.. code-block:: yaml

    ---
    persistence_api:
      class: opentaxii.persistence.sqldb.SQLDatabaseAPI
      parameters:
        db_connection: postgresql://username:P@ssword@db.example.com:5432/databasename
        create_tables: yes

    auth_api:
      class: opentaxii.auth.sqldb.SQLDatabaseAPI
      parameters:
        db_connection: postgresql://username:P@ssword@db.example.com:5432/databasename
        create_tables: yes
        secret: SECRET-STRING-NEEDS-TO-BE-CHANGED


Properties
==========

    - ``domain`` — domain that will be used in service URLs in TAXII responses.
    - ``support_basic_auth`` — enable/disable Basic Authentication support. If disabled, only JWT authentication is allowed.
    - ``save_raw_inbox_message`` — enable/disable storing of raw TAXII Inbox messages via Persistence API's ``create_inbox_message`` method. This is useful for bookkeeping but significantly increases storage requirements.
    - ``xml_parser_supports_huge_tree`` — enable/disable security restrictions in `lxml <http://lxml.de/>`_ library to allow support for very deep trees and very long text content. If this is disabled, OpenTAXII will not be able to parse TAXII messages with content blocks larger than roughly 10MB.
    - ``count_blocks_in_poll_responses`` — enable/disable total count in TAXII Poll responses. It is disabled by default since ``count`` operation might be `very slow <https://wiki.postgresql.org/wiki/Slow_Counting>`_ in some SQL DBs.
    - ``return_server_error_details`` — allow OpenTAXII to return error details in error-status TAXII response.
    - ``persistence_api`` — configuration properties for Persistence API implementation.
    - ``auth_api`` — configuration properties for Authentication API implementation.
    - ``logging`` — logging configuration.
    - ``hooks`` - custom python module with signal subscriptions to import. See :ref:`documentation on custom signals<custom-signals>` and :github-file:`an example <examples/hooks.py>`.


.. _custom-configuration:

Custom configuration
====================

To pass custom configuration to OpenTAXII server, specify an absolute path to your
configuration file in environment variable ``OPENTAXII_CONFIG``.::

	$ export OPENTAXII_CONFIG=/path/to/configuration/file.yml
	
	
This configuration file may fully or partially override default settings.

Example custom configuration:

.. _configuration-example:

.. code-block:: yaml

    ---
    domain: taxii.mydomain.com
    support_basic_auth: no

    persistence_api:
      class: mypackage.opentaxii.CustomPersistenceAPI
      parameters:
        rest_api: http://rest.mydomain.com/api

    auth_api:
      class: opentaxii.auth.sqldb.SQLDatabaseAPI
      parameters:
        db_connection: postgresql://scott:tiger@localhost:5432/mydatabase
        create_tables: yes
        secret: aueHenjitweridUcviapEbsJocdiDrelHonsyorl

    xml_parser_supports_huge_tree: no
    hooks: mypackage.opentaxii.custom_hooks

The built-in implementation of the Persistence and Authentication APIs support SQLite, PostgreSQL, MySQL, and other SQL databases. Check `SQLAlchemy website <http://www.sqlalchemy.org/>`_ to get the full list.

OpenTAXII CLI tools are implemented to call corresponding API methods and support any API implementation.


Services, collections and accounts
==================================

Services, collections and accounts can be created with CLI command ``opentaxii-sync-data`` or with custom code talking to a specific Persistent API implementation/backend.

Step 1
------ 
Create YAML file with collections/services/accounts configuration. See provided example from `OpenTAXII git repo <https://github.com/eclecticiq/OpenTAXII>`_ — file :github-file:`examples/data-configuration.yml <examples/data-configuration.yml>` that contains:

Services:
    * 2 Inbox Services (with ids ``inbox_a`` and ``inbox_b``), 
    * 1 Discovery Service (with id ``discovery_a``),
    * 1 Collection Management Service (with id ``collection_management_a``),
    * 1 Poll Service (with id ``poll_a``).

.. note::
    Services have relative path in the address field, which means OpenTAXII will prepend it with domain configured in server configuration file (``localhost:9000`` in `Default configuration`_).

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
Use ``opentaxii-sync-data`` command to synchorize data configuration in provided file and in DB.

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
Check :doc:`Running OpenTAXII <running>` to see how to run it.

.. rubric:: Next steps

Continue to the :doc:`Running OpenTAXII <running>` page to see how to run OpenTAXII.


.. vim: set spell spelllang=en:
