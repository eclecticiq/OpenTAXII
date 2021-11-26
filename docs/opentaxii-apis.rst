=============
API reference
=============

This document is the API reference for OpenTAXII. It describes all classes,
methods, functions, and attributes that are part of the public API.

Most of the terminology in the OpenTAXII API comes straight from the TAXII specification.
See the `TAXII documentation <https://taxiiproject.github.io/>`_ or `TAXII2 documentation <https://docs.oasis-open.org/cti/taxii/v2.1/os/taxii-v2.1-os.html>`_ for more detailed explanations.


Configuration
=============
.. automodule:: opentaxii.config
    :members:
    :undoc-members:
    :show-inheritance:

TAXII server layer
==================

.. autoclass:: opentaxii.server.TAXIIServer
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: opentaxii.server.TAXII1Server
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: opentaxii.server.TAXII2Server
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: opentaxii.entities
    :members:
    :undoc-members:
    :show-inheritance:

HTTP layer
==========

.. autofunction:: opentaxii.middleware.create_app


Version agnostic TAXII1 entities
================================

.. automodule:: opentaxii.taxii.entities
    :members:
    :undoc-members:
    :show-inheritance:


TAXII services
==============

.. automodule:: opentaxii.taxii.services.abstract
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: opentaxii.taxii.services.discovery
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: opentaxii.taxii.services.inbox
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: opentaxii.taxii.services.poll
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: opentaxii.taxii.services.collection_management
    :members:
    :undoc-members:
    :show-inheritance:


TAXII2 entities
===============

.. automodule:: opentaxii.taxii2.entities
    :members:
    :undoc-members:
    :show-inheritance:


TAXII2 validation
=================

.. automodule:: opentaxii.taxii2.validation
    :members:
    :undoc-members:
    :show-inheritance:
