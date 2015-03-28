=============
Configuration
=============

.. highlight:: sh

This guide provides configuration details for OpenTAXII.

OpenTAXII can be configured using YAML configuration files.

Default configuration
=====================

OpenTAXII ships with the default configuration:

* Default Persistence API and Authentication API implementation are using SQL DB
  as a backend. The sqlite3 databases will be created in ``/tmp/data.db`` and ``/tmp/auth.db``,
  and the tables will be created automatically.
* There are no services and collections configured by default.
* No signal hooks are attached.

Default configuration file looks like this:

.. code-block:: yaml

    ---
    domain: example.com

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
      "": info

    hooks: 


Creating services and collections
=================================

In default configuration OpenTAXII uses SQL DB as a backend. Services and collections can be
created directly in the database or with supplied CLI tools.

Using CLI tools
----------------------------------------------------------

First, YAML files with services and collections configurations needs to be created. You can create your own file
or use examples from OpenTAXII `git repo <https://github.com/Intelworks/OpenTAXII>`_:

* `examples/services.yml <https://raw.githubusercontent.com/Intelworks/OpenTAXII/master/examples/services.yml>`_

  Describes 2 Inbox Services (``inbox_a`` and ``inbox_b``), Discovery Service (``discovery_a``),
  Collection Management Service (``collection_management_a``), and Poll Service (``poll_a``).

  Services have relative path in the address field, which means OpenTAXII will prepend it with
  domain configured in server configuration file (``example.com`` in `default configuration`_).

* `examples/collections.yml <https://raw.githubusercontent.com/Intelworks/OpenTAXII/master/examples/collections.yml>`_

  Lists 4 collections: 
    * ``collection-A`` that accepts all content, with type ``DATA_SET`` and attached to services
      ``inbox_a``, ``collection_management_a``, and ``poll_a``.
    * ``collection-B`` that accepts only content specified in field ``content_bindings``.
    * ``collection-C`` that accepts not only STIX v1.1.1 content but also custom content type ``urn:custom.bindings.com:json:0.0.1``
    * ``collection-D`` that is marked as not available.

To create services run::

  (venv) $ opentaxii-create-services -c services.yaml

To create collections run (services should already exist)::

  (venv) $ opentaxii-create-collections -c collections.yaml

To create an account run::

  (venv) $ opentaxii-create-account -u username -p password

Now OpenTAXII has services and collections configured and can function as a TAXII server.
Check :doc:`Running OpenTAXII <running>` to see how to run it.

To drop the database, just delete sqlite3 database files and restart OpenTAXII server.

Custom configuration
====================

To pass custom configuration to OpenTAXII server, specify an absolute path to your
configuration file in environment variable ``OPENTAXII_CONFIG``. This configuration
file may fully or partially override default settings.

Example custom configuration file:

.. _configuration-example:

.. code-block:: yaml

    ---
    domain: taxii.mydomain.com

    persistence_api:
      class: mypackage.opentaxii.PersistenceAPI
      parameters:
        rest_api: http://rest.mydomain.com

    auth_api:
      class: opentaxii.auth.sqldb.SQLDatabaseAPI
      parameters:
        db_connection: postgresql://scott:tiger@localhost:5432/mydatabase
        create_tables: yes
        secret: mueHenjitweridUnviapEasJocdiDrelHonsyorl

    hooks: mypackage.opentaxii.hooks

Built-in implementations of Persistence and Authentication APIs support SQLite,
PostgreSQL, MySQL, and other databases. Check `SQLAlchemy website <http://www.sqlalchemy.org/>`_
to get the full list.

OpenTAXII CLI tools are implemented to call corresponding API methods and support any API implementation.


.. _custom-api-implementations:

Custom API implementations
==========================

It is possible to attach custom API implementations to OpenTAXII.

Custom API class should inherit base class
(:py:class:`opentaxii.persistence.api.OpenTAXIIPersistenceAPI` for Persistence API and 
:py:class:`opentaxii.auth.api.OpenTAXIIAuthAPI` for Authentication API) and implement all defined methods.

Class constructor can accept any parameters. These parameters (as well as API class full name)
have to be set in OpenTAXII configuration file. See :ref:`example above <configuration-example>` for exact syntax.
OpenTAXII will load the class from the ``PYTHONPATH`` and create API instance during server's start up procedure.

See :doc:`Public code-level APIs <public-apis>` documentation for the details about OpenTAXII APIs.


.. _custom-signals:

Custom signal listeners
=======================

Users can attach custom listeners for the events OpenTAXII emits. See :ref:`Signals <opentaxii-signals>` to find
a list of supported signals.

To attach custom signals, specify full module name as a value for ``hooks`` field in OpenTAXII configuration file.
Note that the module needs to be OpenTAXII's ``PYTHONPATH``.

Example of the implementation is provided in OpenTAXII repository - `examples/hooks.py <https://raw.githubusercontent.com/Intelworks/OpenTAXII/master/examples/hooks.py>`_.


.. rubric:: Next steps

Continue to the :doc:`Running OpenTAXII <running>` page to see how to run OpenTAXII.


.. vim: set spell spelllang=en:
