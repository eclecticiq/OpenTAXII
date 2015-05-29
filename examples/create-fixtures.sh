#!/bin/bash

DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# we're using default OpenTAXII config here

opentaxii-create-services -c $DIR/services.yml
opentaxii-create-collections -c $DIR/collections.yml
