======================
Public code-level APIs
======================

This page describes OpenTAXII's public code-level APIs.

Overview
========

OpenTAXII ships with code-level APIs that can be extended by users. Built-in implementations
use SQL database as a backend (everything that `SQLAlchemy <http://www.sqlalchemy.org/>`_ supports).

Additionaly, OpenTAXII supports anychronous notifications and users can attach custom
listeners to the specific events.

.. _custom-api-implementations:

Custom API implementations
==========================

It is possible to attach custom API implementations to OpenTAXII.

Custom API class should inherit base class
(:py:class:`opentaxii.persistence.api.OpenTAXIIPersistenceAPI` for Persistence API and 
:py:class:`opentaxii.auth.api.OpenTAXIIAuthAPI` for Authentication API) and implement all defined methods.

Class constructor can accept any parameters. These parameters (as well as API class full name)
have to be set in OpenTAXII configuration file. See :ref:`example configuration <configuration-example>` for exact syntax.
OpenTAXII will load the class from the ``PYTHONPATH`` and create API instance during server's start up procedure.

OpenTAXII APIs are documented below.


.. _custom-signals:

Custom signal listeners
=======================

Users can attach custom listeners for the events OpenTAXII emits. See :ref:`Signals <opentaxii-signals>` to find
a list of supported signals.

To attach custom signals, specify full module name as a value for ``hooks`` field in OpenTAXII configuration file.
Note that the module needs to be in OpenTAXII's ``PYTHONPATH``.

Example of the implementation is provided in OpenTAXII repository - `examples/hooks.py <https://raw.githubusercontent.com/eclecticiq/OpenTAXII/master/examples/hooks.py>`_.


Persistence API
===============

Persistence API takes care of all CRUD operations with entities and wraps backend storage layer.

See :doc:`Configuration <configuration>` page for the details about how to attach
custom implementation of Persistence API.

.. automodule:: opentaxii.persistence.api
    :members:
    :undoc-members:
    :show-inheritance:


Authentication API
==================

Authentication API represents an authority for authentication-related queries.

See :doc:`Configuration <configuration>` page for the details about how to attach
custom implementation of Authentication API.

.. automodule:: opentaxii.auth.api
    :members:
    :undoc-members:
    :show-inheritance:


.. _opentaxii-signals:

Signals
=======

Signals provide the ability for the user's code to receive asynchronous notification
for predefined signals. 

See :ref:`Custom signal listeners <custom-signals>` chapter for the details about how to attach
listeners for the signals.

.. automodule:: opentaxii.signals
    :members:
    :undoc-members:
    :show-inheritance:
.. autodata:: CONTENT_BLOCK_CREATED
    :annotation: = Instance of a signal singleton. Signal emitted when new content block is created.
.. autodata:: INBOX_MESSAGE_CREATED
    :annotation: = Instance of a signal singleton. Signal emitted when new inbox message is created.
.. autodata:: SUBSCRIPTION_CREATED
    :annotation: = Instance of a signal singleton. Signal emitted when new subscription is created.

