===========================
Contributing and developing
===========================

.. _OpenTAXII project page: https://github.com/EclecticIQ/OpenTAXII


Reporting issues
================

OpenTAXII uses Github's issue tracker. See the `OpenTAXII project page`_ on Github.


Obtaining the source code
=========================

The OpenTAXII source code can be found on Github. See the `OpenTAXII project page`_.

Layout
======

OpenTAXII repository has the following layout:

* ``docker/`` - Docker configuration files (:doc:`OpenTAXII Docker documentation <docker>`);
* ``docs/`` - used to build the `documentation <http://opentaxii.readthedocs.org>`_;
* ``examples/`` - configuration and code examples;
* ``opentaxii/`` - OpenTAXII source;
* ``tests/`` - opentaxii tests.


Compiling from source
=====================

After cloning the Github repo, just run this::

   (venv) $ python setup.py install


Running the tests
=================

Almost all OpenTAXII code is covered by the unit tests. OpenTAXII uses `py.test <http://pytest.org/latest/>`_ and
`tox <http://tox.readthedocs.org/en/latest/>`_ for running tests. Type ``tox -r`` or ``py.test`` to run the unit tests.


Generating the documentation
============================

The documentation is written in `ReStructuredText <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html>`_ (reST) format and processed
using `Sphinx <http://sphinx-doc.org/>`_. To build HTML documentation, go to ``docs`` and type ``make html``.

.. rubric:: Next steps

Continue to :doc:`License <license>`.

.. vim: set spell spelllang=en:
