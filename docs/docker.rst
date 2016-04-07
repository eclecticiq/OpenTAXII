Docker
======

OpenTAXII can also be run using docker. This guide assumes that you have access to a local or remote docker server, and won't go into the setup of docker.

To get a default (development) instance using docker


.. code-block:: shell

    $ docker run -d -p 9000:9000 eclecticiq/opentaxii

.. note::

    OpenTAXII is now accessible through port 9000, with data stored locally in a SQLite database.


Configuration
-------------

Configuration is done through environment variables.

Common configuration parameters are:

``OPENTAXII_DOMAIN`` : (optional)
    This specifies under which domain the OpenTAXII server is available, default: ``localhost:9000``

--------------------

Setting up  authentication is done with the following two variables:

``OPENTAXII_USER`` : (optional)
      If the OpenTAXII user and password are not set, no authentication is required

``OPENTAXII_PASS`` : (optional)
      If you don't want to specify the password on the command line, it is possible to leave the definition empty, and Docker will pick up the value from the environment.

``OPENTAXII_SECRET`` : (optional)
    This is the secret with which the generated token is encoded.

.. code-block:: shell

    $ export OPENTAXII_PASS="SomePassword"
    $ docker -d -p 9000:9000 -e OPENTAXII_USER=myuser -e OPENTAXII_PASS eclecticiq/opentaxii

---------------------

If you want to use a PostgreSQL database, instead of the included SQLite database, you can use the following environment variables for configuration:

``DATABASE_HOST`` : (required)
    This is the database host to connect to

``DATABASE_PORT`` : (optional)
    Default is ``5432``

``DATABASE_USER`` : (optional)
    If not set, the default ``postgres`` is used.

``DATABASE_PASS`` : (optional)
    If not set, the database can be accessed by all containers on the same host!

``DATABASE_NAME`` : (optional)
    The database to use, by default uses ``postgres``

If you would like to use a different Database for authentication, you can also set the following variables (any variable not set, will use it's regular DB counterpart):

``AUTH_DATABASE_HOST`` : (required)
    This is the database host to connect to

``AUTH_DATABASE_PORT`` : (optional)
    Default is ``5432``

``AUTH_DATABASE_USER`` : (optional)
    If not set, the default ``postgres`` is used.

``AUTH_DATABASE_PASS`` : (optional)
    If not set, the database can be accessed by all containers on the same host!

``AUTH_DATABASE_NAME`` : (optional)
    The database to use, by default uses ``postgres``


Volumes
-------

This docker container exposes two volumes, which can be attached to a running instance:

``/data``
    This volume will contain the SQLite databases used by the default instance.

``/input``
    If you want to pre-load the running instance with `services.yml`, `collections.yml` or have your own `opentaxii.yml` configuration used for the running system, create a folder with these documents present.

.. code-block:: shell

    $ pwd
    /some/path/examples
    $ ls /some/path/examples
    collections.yml services.yml
    $ docker run -d -p 9000:9000 -v /some/path/examples:/input eclecticiq/opentaxii

.. note::
    Make sure your naming is correct. It will only execute actions when any of the files with names: ``services.yml``, ``collections.yml``, or ``opentaxii.yml`` are present.

Extending
---------

If you need custom configuration, and installation of extra/custom code, it is better to extend the OpenTAXII docker image. For example, adding mysql (instead of PostgreSQL), and adding custom code, which is configured in a custom opentaxii.yml. The Dockerfile used will then look something like:

.. code-block:: docker

  FROM eclecticiq/opentaxii:latest
  MAINTAINER EclecticIQ <opentaxii@eclecticiq.com>

  RUN pip install mysql-python \
    && pip install custom-package

  COPY opentaxii.yml /input/opentaxii.yml

And building the image is then done using:

.. code-block:: shell

  $ docker build -t eclecticiq/opentaxii-mysql .


Full Example with Compose
-------------------------

To see a full example of running OpenTAXII against a "real" database, using the `docker-compose <https://docs.docker.com/compose/>`_ tool, checkout the configuration at: `examples/docker-compose.yml <https://raw.githubusercontent.com/EclecticIQ/OpenTAXII/master/examples/docker-compose.yml>`_

.. code-block:: yaml

    db:
      image: postgres:9.4
      environment:
        POSTGRES_USER: user
        POSTGRES_PASSWORD: password
        POSTGRES_DB: opentaxii

    opentaxii:
      image: eclecticiq/opentaxii
      environment:
        OPENTAXII_AUTH_SECRET: secret
        OPENTAXII_DOMAIN: 192.168.59.103:9000
        OPENTAXII_USER: user1
        OPENTAXII_PASS: pass1
        DATABASE_HOST: db
        DATABASE_NAME: opentaxii
        DATABASE_USER: user
        DATABASE_PASS: password
      volumes:
        - ./:/input:ro
      ports:
        - 9000:9000
      links:
        - db:db

This configuration starts two containers: ``opentaxii`` and ``db``, creates the given collections and services, and adds a user for authentication.


.. rubric:: Next steps

Continue to :doc:`Authentication <auth>` page to learn how OpenTAXII authentication process works.



.. vim: set spell spelllang=en:
