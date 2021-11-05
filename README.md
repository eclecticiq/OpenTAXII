# OpenTAXII

TAXII server implementation in Python from [EclecticIQ](https://www.eclecticiq.com).

OpenTAXII is a robust Python implementation of TAXII Services that
delivers rich feature set and friendly pythonic API built on top of well
designed application.

OpenTAXII is guaranteed to be compatible with [Cabby](https://github.com/eclecticiq/cabby), TAXII client library.

[Source](https://github.com/eclecticiq/OpenTAXII) | [Documentation](http://opentaxii.readthedocs.org) | [Information](http://www.eclecticiq.com) | [Download](https://pypi.python.org/pypi/opentaxii/)


[![Build status](https://github.com/eclecticiq/OpenTAXII/actions/workflows/tox.yml/badge.svg?branch=master)](https://github.com/eclecticiq/OpenTAXII/actions/workflows/tox.yml?query=branch%3Amaster+)
[![Coverage Status](https://coveralls.io/repos/eclecticiq/OpenTAXII/badge.svg)](https://coveralls.io/r/eclecticiq/OpenTAXII)
[![Documentation Status](https://readthedocs.org/projects/opentaxii/badge/?version=stable)](https://readthedocs.org/projects/opentaxii/)

## State of the project

We have made the decision to consider this project **feature-complete**. It means we still maintain it, however we focus only on bug fixes. Still, we’re very open to external contributions - if you know how to fix an issue and you can open a PR, we will be very grateful.

## Getting started
See [the documentation](https://opentaxii.readthedocs.io/en/stable/installation.html).

## Getting started with OpenTAXII using Docker

OpenTAXII can also be run using docker. This guide assumes that you have
access to a local or remote docker server, and won't go into the setup
of docker.

To get a default (development) instance using docker

```bash
$ docker run -d -p 9000:9000 eclecticiq/opentaxii
```

To have the instance preloaded with example data, see [the documentation on docker volumes](https://opentaxii.readthedocs.io/en/stable/docker.html#volumes).

> **NOTE:**
> OpenTAXII is now accessible through port 9000, with data stored
> locally in a SQLite databases optionally using services/collections/accounts defined
> in [data-configuration.yml](https://raw.githubusercontent.com/EclecticIQ/OpenTAXII/master/examples/data-configuration.yml)

More documentation on running OpenTAXII in a container is found in the [OpenTAXII Docker Documentation](https://opentaxii.readthedocs.io/en/stable/docker.html).

## Feedback

You are encouraged to provide feedback by commenting on open issues or
sending us email at <opentaxii@eclecticiq.com>

