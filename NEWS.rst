===============
Version history
===============

OpenTAXII 0.1.2
===============

Release date: 2015-07-24

* Docker configuration added.
* Health check endpoint added.
* Basic authentication support added.
* Temporary workaround for https://github.com/TAXIIProject/libtaxii/issues/191.
* Method ``get_domain`` in Persistence API returns domain value configured for ``service_id``. If nothing returned, value set in configuration file will be used.
* Performance optimisations.
* Bug fixes and style improvements.

OpenTAXII 0.1.1
===============

Release date: 2015-04-08

* Alias for Root Logger added to logging configuration.
* Context object in a request scope that holds account and token added.
* Support for OPTIONS HTTP request to enable auto version negotiation added.
* Documentation improved.

OpenTAXII 0.1.0
===============

Release date: 2015-03-31

* Initial release
