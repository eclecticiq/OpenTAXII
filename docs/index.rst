=========
OpenTAXII
=========

OpenTAXII is Python TAXII server implementation from Intelworks.

TAXII (Trusted Automated eXchange of Indicator Information) is a collection of specifications defining a set of services and message exchanges used for sharing cyber threat intelligence information between parties. Check `TAXII homepage <http://taxii.mitre.org/>`_ to get more information.

OpenTAXII's key features are:

- **Rich feature set**

  OpenTAXII implements all TAXII services according to TAXII specification (version 1.0 and 1.1). On
  top of these services, it also delivers additional functionality such as customizable APIs,
  authentication and flexible logging.


- **Designed to be extendable**

  OpenTAXII architecture follows TAXII specification in its idea of TTA (TAXII transport agent)
  and TMH (TAXII message handler) components, separating implementations of:

      - Transport layer (`Flask <flask.pocoo.org>`_ web app with extendable authentication via Authentication API)
      - TAXII logic layer (TAXII server/services/message handlers)
      - Persistence layer (extendable via Persistence API)


.. rubric:: Documentation contents

.. toctree::
   :maxdepth: 2

   installation
   configuration
   running
   auth
   public-apis
   opentaxii-apis
   developer
   news
   license

.. rubric:: External links

* `Online documentation <https://opentaxii.readthedocs.org/>`_ (Read the docs)
* `Project page <https://github.com/Intelworks/OpenTAXII/>`_ with source code and issue tracker (Github)
* `Python Package Index (PyPI) page <http://pypi.python.org/pypi/opentaxii/>`_ with released tarballs
