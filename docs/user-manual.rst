How to use OpenTAXII?
*********************

Requirements
============

* `Docker Engine and Docker Compose <https://docs.docker.com/engine/install/>`__
* `taxii2-client <https://taxii2client.readthedocs.io/en/latest/>`__ (for TAXII 2.1)

Run OpenTAXII
=================

#.  Create the ``opentaxii.yml`` file and fill it in with the following:

    ..  code-block:: yaml

        ---
        domain: "localhost:9000"
        support_basic_auth: yes

        auth_api:
          class: opentaxii.auth.sqldb.SQLDatabaseAPI
          parameters:
            db_connection: sqlite:////tmp/auth.db
            create_tables: yes
            secret: <secret_password1>

        taxii1:

        taxii2:
          persistence_api:
            class: opentaxii.persistence.sqldb.Taxii2SQLDatabaseAPI
            parameters:
              db_connection: sqlite:////data/data.db
              create_tables: yes
          title: "My OpenTAXII Server"
          description: "My OpenTAXII server runs with TAXII 2"
          max_content_length: 209715200
          public_discovery: true

    Change the value for the secret to a more secure value.

#.  Create a ``docker-compose.yml`` file and fill it in with the following:

    ..  code-block:: yaml
    
        version: '3.8'
        services:
          opentaxii:
            image: eclecticiq/opentaxii
            volumes:
              - ./:/input:ro
            ports:
              - 9000:9000

#.  Run Docker Compose.

    ..  code-block:: bash

        docker compose -f docker-compose.yml up

#.  Stop Docker Compose using ``Ctrl + C``.

    .. Note::

    Alternatively, add the ``-d`` flag to run Docker Compose in the background.
    In that case, run ``docker compose --env-file .env -f docker-compose.yml down`` to stop OpenTAXII.

Configure OpenTAXII
===================

#.  Create a ``data-configuration.yml`` file and fill it in with the following:

    ..  code-block:: yaml
    
        ---

        accounts:
          - username: user1
            password: <secret_password2>

    Change the value for the passwords to more secure values.

#.  Open a shell session into your OpenTAXII container

    ..  code-block:: bash

        docker exec -it test-opentaxii-1 bash

#.  Run ``opentaxii-sync-data`` with the ``data-configuration.yml`` file.

    ..  code-block:: bash
      
        opentaxii-sync-data -f /input/data-configuration.yaml

Interact with OpenTAXII
=======================

#.  In a Python shell, import the `taxii2client` library.

    ..  code-block:: python

        import taxii2client

#.  Connect to your OpenTAXII Server.

    .. code-block:: python

        server = taxii2client.Server(url='http://localhost:9000/taxii2/',
                                     user='user1',
                                     password='<same-password-set-in-data-configuration')

#.  Print your server's information.

    ..  code-block:: python

        print(server.title)
