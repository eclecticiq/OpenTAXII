Changelog
=========

0.1.9 (2017-06-19)
------------------
* `libtaxii <https://github.com/TAXIIProject/libtaxii>`_ dependency upgraded to 1.1.111.
* Various bug fixes and improvements (thanks to `@bjigmp <https://github.com/bjigmp>`_, `@chorsley <https://github.com/chorsley>`_, `@rjprins <https://github.com/rjprins>`_).

0.1.8 (2017-02-21)
------------------
* Ability to enable/disable "huge trees" support in XML parser. Configuration property `xml_parser_supports_huge_tree` set to `yes` or `true` will disable security restrictions and force XML parser to support very deep trees and very long text content.
* Adjust SQL Persistence API implemetation so it works smoothly with MySQL backend.
* Use Python 3.5 instead of Python 3.4 for tests.

0.1.7 (2016-10-18)
------------------
* Minor fixes.
* Dependencies were changed from hard-pinned to more flexible.
* Example of production DB configuration added to docs.

0.1.6 (2016-06-01)
------------------
* Python 3.4 compatibility of the codebase. Tox configuration extended with python 3.4 environment run.
* Flake8 full style compatibility. Flake8 check added to Tox configuration.
* SQLAlchemy session scope issue fixed (related to `#38 <https://github.com/EclecticIQ/OpenTAXII/issues/38>`_).
* `opentaxii-delete-blocks` CLI command added (related to `#45 <https://github.com/EclecticIQ/OpenTAXII/issues/45>`_).
* `delete_content_blocks` method `added <https://github.com/EclecticIQ/OpenTAXII/commit/dc6fddc27a98e8450c7e05e583b2bfb741f6e197#diff-6814849ac352b2b74132f8fa52e0ec4eR213>`_ to Persistence API.
* Collection's name is `required <https://github.com/EclecticIQ/OpenTAXII/commit/dc6fddc27a98e8450c7e05e583b2bfb741f6e197#diff-ce3f7b939e5c540480ac655aef32c513R116>`_ to be unique in default SQL DB Auth API implementation.

0.1.5 (2016-03-15)
------------------
* Fix for the issue with persistence backend returning ``None`` instead of ``InboxMessage`` object

0.1.4 (2016-02-25)
------------------
* Hard-coded dependencies in ``setup.py`` removed.

0.1.3 (2016-02-25)
------------------
* Versions of dependencies are pinned.
* Code adjusted for a new version of `anyconfig <https://pypi.python.org/pypi/anyconfig>`_ API.
* Test for configuration loading added.

0.1.2 (2015-07-24)
------------------
* Docker configuration added.
* Health check endpoint added.
* Basic authentication support added.
* Temporary workaround for `Issue #191 <https://github.com/TAXIIProject/libtaxii/issues/191>`_.
* Method ``get_domain`` in Persistence API returns domain value configured for ``service_id``. If nothing returned, value set in configuration file will be used.
* Performance optimisations.
* Bug fixes and style improvements.

0.1.1 (2015-04-08)
------------------
* Alias for Root Logger added to logging configuration.
* Context object in a request scope that holds account and token added.
* Support for OPTIONS HTTP request to enable auto version negotiation added.
* Documentation improved.

0.1.0 (2015-03-31)
------------------
* Initial release
