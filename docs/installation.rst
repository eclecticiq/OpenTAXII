==================
Installation guide
==================

.. highlight:: sh

This guide provides installation instructions for OpenTAXII.


Build and install OpenTAXII
========================

The recommended (and easiest) way to install OpenTAXII is to install it into a
virtual environment (*virtualenv*)::

   $ virtualenv envname
   $ source envname/bin/activate

Now you can automatically install the latest OpenTAXII release from the `Python
Package Index <http://pypi.python.org/>`_ (PyPI) using ``pip``::

   (envname) $ pip install opentaxii

(In case you're feeling old-fashioned:: downloading a source tarball, unpacking
it and installing it manually with ``python setup.py install`` should also
work.)


Versioning
==========

Releases of OpenTAXII are given major.minor.revision version numbers, where major and minor correspond to the roadmap Intelworks has. The revision` number is used to indicate a fixpack.


Start OpenTAXII
===============

After installation, this command should not give any output::

   (envname) $ python fixtures.py
   (envname) $ python runner.py


.. rubric:: Next steps

Continue with the :doc:`user guide <user>` to see how to use OpenTAXII.

.. vim: set spell spelllang=en:
