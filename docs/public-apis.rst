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

:ref:`Custom API implementations <custom-api-implementations>` chapter describes how API implementations
can be attached to OpenTAXII.

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

