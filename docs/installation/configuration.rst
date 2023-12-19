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
    - There is only taxii1 support, taxii2 is disabled


Default configuration file looks like this:

.. code-block:: yaml

    ---
    domain: "localhost:9000"

    support_basic_auth: yes
    return_server_error_details: no

    auth_api:
      class: opentaxii.auth.sqldb.SQLDatabaseAPI
      parameters:
        db_connection: sqlite:////tmp/auth.db
        create_tables: yes
        secret: SECRET-STRING-NEEDS-TO-BE-CHANGED
        token_ttl_secs: 3600

    taxii1:
      save_raw_inbox_messages: yes
      xml_parser_supports_huge_tree: yes
      count_blocks_in_poll_responses: no
      unauthorized_status: UNAUTHORIZED
      hooks:
      persistence_api:
        class: opentaxii.persistence.sqldb.SQLDatabaseAPI
        parameters:
          db_connection: sqlite:////tmp/data.db
          create_tables: yes

    taxii2:

    logging:
      opentaxii: info
      root: info

.. note::
  OpenTAXII uses a SQLite Database by default wich is intended only when running OpenTAXII in a development environment. Please use different SQL DB backend for running in a production environment.

An example of custom configuration that allows OpenTAXII to connect to production-ready PostgreSQL database:

.. code-block:: yaml

    ---
    auth_api:
      class: opentaxii.auth.sqldb.SQLDatabaseAPI
      parameters:
        db_connection: postgresql://username:P@ssword@db.example.com:5432/databasename
        create_tables: yes
        secret: SECRET-STRING-NEEDS-TO-BE-CHANGED

    taxii1:
      persistence_api:
        class: opentaxii.persistence.sqldb.SQLDatabaseAPI
        parameters:
          db_connection: postgresql://username:P@ssword@db.example.com:5432/databasename
          create_tables: yes


Properties
==========

    - ``domain`` — domain that will be used in service URLs in TAXII responses.
    - ``support_basic_auth`` — enable/disable Basic Authentication support. If disabled, only JWT authentication is allowed.
    - ``return_server_error_details`` — allow OpenTAXII to return error details in error-status TAXII response.
    - ``auth_api`` — configuration properties for Authentication API implementation.

      - ``class`` — the full import name of the class to use
      - ``parameters`` — the parameters used to instantiate the class

        - ``db_connection`` — the database connetion string
        - ``create_tables`` — boolean, if true, create tables on startup
        - ``secret`` — the secret with which the generated tokens are encoded
        - ``token_ttl_secs`` — time that generated tokens are valid

    - ``taxii1`` — taxii1-specific settings

      - ``save_raw_inbox_message`` — enable/disable storing of raw TAXII Inbox messages via Persistence API's ``create_inbox_message`` method. This is useful for bookkeeping but significantly increases storage requirements.
      - ``xml_parser_supports_huge_tree`` — enable/disable security restrictions in `lxml <http://lxml.de/>`_ library to allow support for very deep trees and very long text content. If this is disabled, OpenTAXII will not be able to parse TAXII messages with content blocks larger than roughly 10MB.
      - ``count_blocks_in_poll_responses`` — enable/disable total count in TAXII Poll responses. It is disabled by default since ``count`` operation might be `very slow <https://wiki.postgresql.org/wiki/Slow_Counting>`_ in some SQL DBs.
      - ``unauthorized_status`` — TAXII status type for authorization error. "UNAUTHORIZED" by default. see `libtaxii.constants.ST_TYPES_11 <https://libtaxii.readthedocs.io/en/stable/api/constants.html#libtaxii.constants.ST_TYPES_11>`_ for the list of available values.
      - ``hooks`` - custom python module with signal subscriptions to import. See :ref:`documentation on custom signals<custom-signals>` and :github-file:`an example <examples/hooks.py>`.
      - ``persistence_api`` — configuration properties for Persistence API implementation.

        - ``class`` — the full import name of the class to use
        - ``parameters`` — the parameters used to instantiate the class

          - ``db_connection`` — the database connetion string
          - ``create_tables`` — boolean, if true, create tables on startup

    - ``taxii2`` — taxii2-specific settings

      - ``persistence_api`` — configuration properties for Persistence API implementation.

        - ``class`` — the full import name of the class to use
        - ``parameters`` — the parameters used to instantiate the class

          - ``db_connection`` — the database connetion string
          - ``create_tables`` — boolean, if true, create tables on startup

      - ``max_content_length`` — the maximum size of the request body in bytes that the server can support
      - ``allow_custom_properties`` — boolean, if true, allow custom stix2 properties when posting objects (default: true)

    - ``logging`` — logging configuration.


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

    auth_api:
      class: opentaxii.auth.sqldb.SQLDatabaseAPI
      parameters:
        db_connection: postgresql://scott:tiger@localhost:5432/mydatabase
        create_tables: yes
        secret: aueHenjitweridUcviapEbsJocdiDrelHonsyorl

    taxii1:
      xml_parser_supports_huge_tree: no
      hooks: mypackage.opentaxii.custom_hooks
      persistence_api:
        class: mypackage.opentaxii.CustomPersistenceAPI
        parameters:
          rest_api: http://rest.mydomain.com/api

The built-in implementation of the Persistence and Authentication APIs support SQLite, PostgreSQL, MySQL, and other SQL databases. Check `SQLAlchemy website <http://www.sqlalchemy.org/>`_ to get the full list.

OpenTAXII CLI tools are implemented to call corresponding API methods and support any API implementation.

Environment variables configuration
===================================

You can (re)define any configuration option with environment variables. Start variable name with ``OPENTAXII_``. Use ``__`` to separate parts of the config path. Use uppercase. Specify values in YAML syntax.

.. code-block:: bash

    export OPENTAXII_DOMAIN='taxii.mydomain.com'
    export OPENTAXII_SUPPORT_BASIC_AUTH='no'
    export OPENTAXII__PERSISTENCE_API__CLASS='mypackage.opentaxii.CustomPersistenceAPI'
    export OPENTAXII__AUTH_API__PARAMETERS__SECRET='aueHenjitweridUcviapEbsJocdiDrelHonsyorl'

Environment variables applied after all other configs and can be used to redefine any option.

.. rubric:: Next steps

Continue to the :doc:`Running OpenTAXII <running>` page to see how to run OpenTAXII.

.. vim: set spell spelllang=en:
