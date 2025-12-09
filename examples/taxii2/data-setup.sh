#!/bin/bash
opentaxii-add-api-root --title Default --description "The default API root" \
    --default --public --id b96631e7-f1c1-43dd-b9d6-55d634f31c41
opentaxii-add-collection --rootid b96631e7-f1c1-43dd-b9d6-55d634f31c41 \
    --title "A collection" --public
opentaxii-create-account --username admin --password admin --admin