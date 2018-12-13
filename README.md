# OpenTAXII

TAXII server implementation in Python from [EclecticIQ](https://www.eclecticiq.com).

OpenTAXII is a robust Python implementation of TAXII Services that
delivers rich feature set and friendly pythonic API built on top of well
designed application.

OpenTAXII is guaranteed to be compatible with [Cabby](https://github.com/eclecticiq/cabby), TAXII client library.

[Source](https://github.com/eclecticiq/OpenTAXII) | [Documentation](http://opentaxii.readthedocs.org) | [Information](http://www.eclecticiq.com) | [Download](https://pypi.python.org/pypi/opentaxii/)


[![Build Status](https://travis-ci.org/eclecticiq/OpenTAXII.svg?branch=move_docs)](https://travis-ci.org/eclecticiq/OpenTAXII)
[![Coverage Status](https://coveralls.io/repos/eclecticiq/OpenTAXII/badge.svg)](https://coveralls.io/r/eclecticiq/OpenTAXII)
[![Documentation Status](https://readthedocs.org/projects/opentaxii/badge/?version=stable)](https://readthedocs.org/projects/opentaxii/)

## Getting started
See [the documentation](https://opentaxii.readthedocs.io/en/stable/installation.html).

## Getting started with OpenTAXII using Docker

OpenTAXII can also be run using docker. This guide assumes that you have
access to a local or remote docker server, and won’t go into the setup
of docker.

To get a default (development) instance using docker

```bash
$ docker run -d -p 9000:9000 eclecticiq/opentaxii
```

> **NOTE:**
> OpenTAXII is now accessible through port 9000, with data stored
> locally in a SQLite databases using services/collections/accounts defined
> in [data-configuration.yml](https://raw.githubusercontent.com/EclecticIQ/OpenTAXII/master/examples/data-configuration.yml)

More documentation on running OpenTAXII in a container is found in the [OpenTAXII Docker Documentation](https://opentaxii.readthedocs.io/en/stable/docker.html).

## Feedback

You are encouraged to provide feedback by commenting on open issues or
sending us email at <opentaxii@eclecticiq.com>

