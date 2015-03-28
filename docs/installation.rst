==================
Installation guide
==================

.. highlight:: sh

This guide provides installation instructions for OpenTAXII.


Build and install OpenTAXII
===========================

The recommended (and easiest) way to install OpenTAXII is to install it into a
virtual environment (*virtualenv*)::

   $ virtualenv venv
   $ source venv/bin/activate

Now you can automatically install the latest OpenTAXII release from the `Python
Package Index <http://pypi.python.org/>`_ (PyPI) using ``pip``::

   (venv) $ pip install opentaxii

.. note::
    Since OpenTAXII has `libtaxii <https://github.com/TAXIIProject/libtaxii>`_ as a dependency, the system libraries
    `libtaxii` requires needs to be installed. Check
    `libtaxii documentation <http://libtaxii.readthedocs.org/en/latest/installation.html#dependencies>`_ for the details.

To install OpenTAXII from source files: download a tarball, unpack it and install it manually with ``python setup.py install``.


Versioning
==========

Releases of OpenTAXII are given major.minor.revision version numbers, where major and minor correspond to the roadmap Intelworks has. The revision number is used to indicate a bug fix only release.


.. rubric:: Next steps

Continue with the :doc:`Configuration <configuration>` page to see how to configure OpenTAXII.

.. vim: set spell spelllang=en:
