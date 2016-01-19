============
Installation
============

.. highlight:: sh

Install Python
--------------

OpenTAXII works with Python version 2.7, which you can download `here <http://www.python.org/download/>`_ or with your operating system’s package manager. 

You can verify that Python is installed by typing ``python`` from your shell; you should see something like::

	$ python
	Python 2.7.6 (default, Sep  9 2014, 15:04:36) 
	[GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.39)] on darwin
	Type "help", "copyright", "credits" or "license" for more information.
	>>> 

Install OpenTAXII
-----------------
To sandbox the project and protect system-wide python it is recommended to install OpenTAXII into a `virtual environment <https://virtualenv.pypa.io/en/latest/installation.html>`_ (*virtualenv*)::

Create a virtual environment named venv::

   $ virtualenv venv

Where ``venv`` is a directory to place the new environment

Activate this environment::

   $ . venv/bin/activate
   (venv) $
   
Now install the latest OpenTAXII release from the `Python
Package Index <http://pypi.python.org/>`_ (PyPI) using ``pip``::  
 
   (venv) $ pip install opentaxii

Without the virtual environment it's just::

   $ pip install opentaxii

.. note::
    Since OpenTAXII has `libtaxii <https://github.com/TAXIIProject/libtaxii>`_ as a dependency, the system libraries
    `libtaxii` will be installed. Check
    `libtaxii documentation <http://libtaxii.readthedocs.org/en/latest/installation.html#dependencies>`_ for the details.

To install OpenTAXII from source files: download tarball, unpack it and install it manually with::

   $ python setup.py install


Versioning
----------

Releases of OpenTAXII are given major.minor.revision version numbers, where major and minor correspond to the roadmap EclecticIQ has. The revision number is used to indicate a bug fix only release.


.. rubric:: Next steps

Continue to :doc:`Configuration <configuration>` page to learn how to configure OpenTAXII.

.. vim: set spell spelllang=en:
