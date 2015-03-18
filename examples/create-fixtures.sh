
DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

export TAXII_SERVER_CONFIG=$DIR/config.yml

opentaxii-create-services -c $DIR/services.yml
opentaxii-create-collections -c $DIR/collections.yml
