# OpenTAXII

TAXII server implementation in Python from [EclecticIQ](https://www.eclecticiq.com).


[Source] (https://github.com/Intelworks/OpenTAXII) | [Documentation](http://opentaxii.readthedocs.org) | [Information](http://www.eclecticiq.com) | [Download] (https://pypi.python.org/pypi/opentaxii/)


[![Build Status](https://travis-ci.org/Intelworks/OpenTAXII.svg?branch=move_docs)](https://travis-ci.org/Intelworks/OpenTAXII)
[![Code Health](https://landscape.io/github/Intelworks/OpenTAXII/master/landscape.svg?style=flat)](https://landscape.io/github/Intelworks/OpenTAXII/master)
[![Coverage Status](https://coveralls.io/repos/Intelworks/OpenTAXII/badge.svg)](https://coveralls.io/r/Intelworks/OpenTAXII)
[![Documentation Status](https://readthedocs.org/projects/opentaxii/badge/?version=latest)](https://readthedocs.org/projects/opentaxii/)

OpenTAXII is a robust Python implementation of TAXII Services that
delivers rich feature set and friendly pythonic API built on top of well
designed application.

## Getting started Using Docker

OpenTAXII can also be run using docker. This guide assumes that you have
access to a local or remote docker server, and won’t go into the setup
of docker.

To get a default (development) instance using docker

``` {.sourceCode .shell}
$ docker run -d -p 9000:9000 intelworks/opentaxii
```

> **NOTE:**
> OpenTAXII is now accessible through port 9000, with data stored
> locally in a SQLite database, and no authentication, using services defined
> in [services.yml](https://raw.githubusercontent.com/Intelworks/OpenTAXII/master/examples/services.yml) 
> and collections from [collections.yml](https://raw.githubusercontent.com/Intelworks/OpenTAXII/master/examples/collections.yml)

More documentation on running OpenTAXII in a container is found in the [OpenTAXII Docker Documentation](http://opentaxii.readthedocs.org/en/latest/docker.html).

## Feedback

You are encouraged to provide feedback by commenting on open issues or
sending us email at <opentaxii@eclecticiq.com>

