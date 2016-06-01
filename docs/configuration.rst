=============
Configuration
=============

.. highlight:: sh

OpenTAXII can be configured using YAML configuration files, it ships with the following `default configuration <https://github.com/eclecticiq/OpenTAXII/blob/master/opentaxii/defaults.yml>`_:

* Persistence API and Authentication API use SQL DB as a backend.
* The sqlite3 databases and corresponding tables will automatically be created in ``/tmp/data.db`` and ``/tmp/auth.db``.
* There are no services and collections configured by default.
* No signal hooks are attached.

Default configuration looks like this:

.. code-block:: yaml

    ---
    domain: "localhost:9000"
    support_basic_auth: yes

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
	 OpenTAXII uses a SQLite Database by default wich is intended only when running OpenTAXII in a development environment. Please change when running in a production environment.

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

The built-in implementation of the Persistence and Authentication APIs support SQLite, PostgreSQL, MySQL, and other databases. Check `SQLAlchemy website <http://www.sqlalchemy.org/>`_
to get the full list.

OpenTAXII CLI tools are implemented to call corresponding API methods and support any API implementation.



Creating services and collections
=================================

Services and collections can be created with supplied CLI tools. It is also possible to directly create them in the DB, but this is out of scope for this guide.

Step 1
------ 
We will need to create YAML files with services and collections configurations. You can create your own file or use examples from `OpenTAXII git repo <https://github.com/eclecticiq/OpenTAXII>`_:

* `examples/services.yml <https://raw.githubusercontent.com/eclecticiq/OpenTAXII/master/examples/services.yml>`_

  Describes the following services:
    * 2 Inbox Services (``inbox_a`` and ``inbox_b``), 
    * Discovery Service (``discovery_a``),
    * Collection Management Service (``collection_management_a``),
    * and Poll Service (``poll_a``).

  Services have relative path in the address field, which means OpenTAXII will prepend it with domain configured in server configuration file (``localhost:9000`` in `default configuration`_).

* `examples/collections.yml <https://raw.githubusercontent.com/eclecticiq/OpenTAXII/master/examples/collections.yml>`_

  Lists 4 collections: 
    * ``collection-A`` that accepts all content, with type ``DATA_SET`` and attached to services
      ``inbox_a``, ``collection_management_a``, and ``poll_a``.
    * ``collection-B`` that accepts only content specified in field ``content_bindings``.
    * ``collection-C`` that accepts not only STIX v1.1.1 content but also custom content type ``urn:custom.bindings.com:json:0.0.1``
    * ``collection-D`` that is marked as not available.

Step 2
------
We create the actual services and collections with the CLI tools.

To create the services run::

  (venv) $ opentaxii-create-services -c services.yml

Next we create the collections (services should already exist!)::

  (venv) $ opentaxii-create-collections -c collections.yml

To create an account run::

  (venv) $ opentaxii-create-account -u username -p password
  
.. note::
	Without an account you can't access services with `authentication_required: yes`  

.. important::
    It is up to Persistence API implementation to control access to the entities. Built-in API implementation **does not** support any
    access control.

Now OpenTAXII has services and collections configured and can function as a TAXII server.
Check :doc:`Running OpenTAXII <running>` to see how to run it.

.. note::
	To drop the database, just delete sqlite3 database files ``/tmp/data.db``, ``/tmp/auth.db`` and restart OpenTAXII server.


.. rubric:: Next steps

Continue to the :doc:`Running OpenTAXII <running>` page to see how to run OpenTAXII.


.. vim: set spell spelllang=en:
