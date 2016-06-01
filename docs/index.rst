=========
OpenTAXII
=========

Latest stable release is v0.1.6. (:doc:`Changelog <changes>`)

..
    Release v\ |version|. (:doc:`Changelog <changes>`)

OpenTAXII is a robust Python implementation of TAXII Services that delivers rich feature set and friendly pythonic API.

TAXII (Trusted Automated eXchange of Indicator Information) is a collection of specifications defining a set of services and message exchanges used for sharing cyber threat intelligence information between parties. Check `TAXII homepage <https://taxiiproject.github.io/>`_ for more information.

**Rich feature set**

OpenTAXII implements all TAXII services according to TAXII specification (version 1.0 and 1.1). On top of these services, it also delivers additional functionality such as;

- customizable APIs,
- authentication,
- flexible logging.


**Designed to be extendable**

OpenTAXII architecture follows TAXII specification in its idea of TTA (TAXII transport agent) and TMH (TAXII message handler) components, separating implementations of:

      - Transport layer (`Flask <flask.pocoo.org>`_ based web app)
      - TAXII logic layer (TAXII server/services/message handlers)
      - Persistence layer (extendable Persistence API)
      - Authentication layer (extendable Authentication API)


.. rubric:: Documentation contents

.. toctree::
   :maxdepth: 1

   installation
   configuration
   running
   docker
   auth
   public-apis
   opentaxii-apis
   developer
   changes
   license

.. rubric:: External links

* `Online documentation <https://opentaxii.readthedocs.org/>`_ (Read the docs)
* `Project page <https://github.com/EclecticIQ/OpenTAXII/>`_ with source code and issue tracker (Github)
* `Python Package Index (PyPI) page <http://pypi.python.org/pypi/opentaxii/>`_ with released tarballs
* `EclecticIQ <https://www.eclecticiq.com>`_
