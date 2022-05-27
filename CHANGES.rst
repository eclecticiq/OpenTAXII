Changelog
=========

0.7.0 (2022-05-27)
------------------
* Nest taxii2 endpoints under `/taxii2/`

0.6.0 (2022-05-25)
------------------
* Add `public_discovery` option to taxii2 config
* Add support for publicly readable taxii 2 api roots

0.5.0 (2022-05-24)
------------------
* Add support for publicly readable taxii 2 collections

0.4.0 (2022-05-20)
------------------
* Move next_param handling into `OpenTAXII2PersistenceAPI`

0.3.0 (2022-04-13)
------------------
* Implement taxii2.1 support

0.3.0a4 (2022-04-13)
--------------------
* Merge changes from 0.2.4 maintenance release

0.3.0a3 (2022-01-21)
--------------------
* Fix bug that prevented booting with only taxii1 config (`#217 <https://github.com/eclecticiq/OpenTAXII/issues/217>`_ thanks `@azurekid <https://github.com/azurekid>`_ for the report)

0.3.0a2 (2021-12-27)
--------------------
* Merge changes from 0.2.3 maintenance release

0.3.0a1
-------
* Add python 3.10 support

0.3.0a0
-------
* Enablement for future taxii2 implementation
* Fix documentation build issues

0.2.4 (2022-04-13)
------------------
* Make sure werkzeug <2.1 and >=2.1 work correctly with auth system

0.2.3 (2021-12-22)
------------------
* Fix bug in multithreaded use of sqlite (`#210 <https://github.com/eclecticiq/OpenTAXII/issues/210>`_ thanks `@rohits144 <https://github.com/rohits144>`_ for the report)

0.2.2 (2021-11-05)
------------------
* Fix readthedocs build

0.2.1 (2021-11-03)
------------------
* Add tests for python 3.6, 3.7, 3.8, 3.9, pypy
* Add tests for sqlite, mysql, mariadb, postgresql
* Fix bug that broke ``delete_content_blocks`` when using mysql on sqlalchemy 1.3
* Docs: Add db schema diagram
* Docs: Clarify how to get default data in a default (development) docker instance
* Fix implicit routing in TAXII 1.1 Inboxes
* Update jwt usage to pyjwt >= 2.0 (thanks `@SanyaKapoor <https://github.com/SanyaKapoor>`_)

0.2.0 (2020-06-30)
------------------
* Enforce UTC usage in datetime fields in SQL DB Persistence API.
* `Fix for #114 <https://github.com/eclecticiq/OpenTAXII/issues/114>`_: reintroduce ``opentaxii-create-account`` CLI command.
* `Fix for #153 <https://github.com/eclecticiq/OpenTAXII/issues/152>`_: check if user can modify a collection before advertising it over inbox service.
* Multiple coding style fixes.
* Various documentation updates.

0.1.12 (2019-03-06)
-------------------
* Remove unnecessary print statements.

0.1.11 (2019-02-13)
-------------------
* Make JSON logging consistent when the application is run via Gunicorn.
* Set ``acceptable_destination`` key in status details instead of extended headers
* Allow passing ``engine_parameters`` to ``SQLDatabaseAPI`` for those who want to customize SQLAlchemy engine parameters.
* Require recent version of ``lxml`` for security reasons.
* Various test and Docker infrastructure improvements.

0.1.10 (2018-06-03)
-------------------
* Replace separate service/collection/account creation process with single ``opentaxii-sync-data`` CLI command.
* Persistence and Auth APIs extended with missing CRUD methods, that are used by ``opentaxii-sync-data``.
* Read/modify collection level ACL added.
* DB models for default implementation of Persistence API and Auth API were changed. No automatic migration code is provided (sorry!), so upgrading might require manual DB migration.
* Drop python2.7 from testing scope.
* Various bug fixes and improvements.

0.1.9 (2017-06-19)
------------------
* `libtaxii <https://github.com/TAXIIProject/libtaxii>`_ dependency upgraded to 1.1.111.
* Various bug fixes and improvements (thanks to `@bjigmp <https://github.com/bjigmp>`_, `@chorsley <https://github.com/chorsley>`_, `@rjprins <https://github.com/rjprins>`_).

0.1.8 (2017-02-21)
------------------
* Ability to enable/disable "huge trees" support in XML parser. Configuration property ``xml_parser_supports_huge_tree`` set to ``yes`` or ``true`` will disable security restrictions and force XML parser to support very deep trees and very long text content.
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
