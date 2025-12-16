#!/bin/bash


trap "echo 'Shutting down OpenTAXII' && exit" EXIT SIGINT SIGTERM

function wait_for_port() {
    (echo >/dev/tcp/$1/$2) &>/dev/null
    while [ $? -ne 0 ];
    do
        echo "Waiting for $1:$2 to become available"
        sleep 1
        (echo >/dev/tcp/$1/$2) &>/dev/null
    done
    echo "$1:$2 is now open"
}

# Default OpenTAXII Configuration
: ${OPENTAXII_DOMAIN:=localhost:9000}
: ${DOCKER_OPENTAXII_AUTH_SECRET:=notVerySecret}
: ${OPENTAXII_CONFIG:=/opentaxii.yml}
# make sure this env var is available to the main process and subprocesses!
export OPENTAXII_CONFIG

# Database Defaults
P_URL="sqlite:////data/data.db"
A_URL="sqlite:////data/auth.db"
: ${DATABASE_USER:=""}
: ${DATABASE_PASS:=""}
: ${DATABASE_HOST:=""}
: ${DATABASE_NAME:=""}
: ${DATABASE_PORT:=5432}
: ${DATABASE_TYPE:=postgresql}
: ${AUTH_DATABASE_USER:=$DATABASE_USER}
: ${AUTH_DATABASE_PASS:=$DATABASE_PASS}
: ${AUTH_DATABASE_HOST:=$DATABASE_HOST}
: ${AUTH_DATABASE_NAME:=$DATABASE_NAME}
: ${AUTH_DATABASE_PORT:=$DATABASE_PORT}
: ${AUTH_DATABASE_TYPE:=$DATABASE_TYPE}

SQL_TEMPL="_type_://_auth__host__port_/_db_"
if [ "${DATABASE_HOST}" ]
then
    [ "$DATABASE_USER" -a "$DATABASE_PASS" ] &&  AUTH="${DATABASE_USER}:${DATABASE_PASS}@"
    URL=${SQL_TEMPL/_auth_/${AUTH-}}
    URL=${URL/_port_/:${DATABASE_PORT}}
    URL=${URL/_host_/${DATABASE_HOST}}
    URL=${URL/_type_/${DATABASE_TYPE}}
    URL=${URL/_db_/${DATABASE_NAME}}
    P_URL=$URL
fi

if [ "${AUTH_DATABASE_HOST}" ]
then
    [ "$AUTH_DATABASE_USER" -a "$AUTH_DATABASE_PASS" ] &&  AUTH="${AUTH_DATABASE_USER}:${AUTH_DATABASE_PASS}@"

    URL=${SQL_TEMPL/_auth_/${AUTH-}}
    URL=${URL/_port_/:${AUTH_DATABASE_PORT}}
    URL=${URL/_host_/${AUTH_DATABASE_HOST}}
    URL=${URL/_type_/${AUTH_DATABASE_TYPE}}
    URL=${URL/_db_/${AUTH_DATABASE_NAME}}
    A_URL=$URL
fi

tmpConfig='/tmp/opentaxii.yml'
cat > "$tmpConfig" <<-EOCONFIG
---

domain: "${OPENTAXII_DOMAIN}"

taxii1:
  persistence_api:
    class: opentaxii.persistence.sqldb.SQLDatabaseAPI
    parameters:
      db_connection: ${P_URL}
      create_tables: yes

taxii2:
  persistence_api:
    class: opentaxii.persistence.sqldb.Taxii2SQLDatabaseAPI
    parameters:
      db_connection: ${P_URL}
      create_tables: yes
  title: "TAXII2 Server"
  public_discovery: true
  max_content_length: 209715200

auth_api:
  class: opentaxii.auth.sqldb.SQLDatabaseAPI
  parameters:
    db_connection: ${A_URL}
    create_tables: yes
    secret: ${DOCKER_OPENTAXII_AUTH_SECRET}

logging:
  opentaxii: info
  root: info

hooks:
EOCONFIG
cp -f $tmpConfig /opentaxii.yml

# Lets see if there is an override
[ -f /input/opentaxii.yml ] && cp -f /input/opentaxii.yml /opentaxii.yml

# Wait for port to become available in case of SQL
[ "$DATABASE_HOST" ] && wait_for_port $DATABASE_HOST ${DATABASE_PORT-5432}
[ "$AUTH_DATABASE_HOST" ] && wait_for_port $AUTH_DATABASE_HOST ${AUTH_DATABASE_PORT-5432}

# Sync data configuration if it is present
[ -f /input/data-configuration.yml ] && opentaxii-sync-data -f /input/data-configuration.yml

# TAXII 2.x Setup - Create API Root and Collection with fixed IDs
: ${TAXII2_API_ROOT_ID:=00000000-0000-0000-0000-000000000001}
: ${TAXII2_COLLECTION_ID:=00000000-0000-0000-0000-000000000002}

echo "Setting up TAXII 2.x API Root and Collection..."

# Create API Root (ignore error if already exists)
opentaxii-add-api-root \
    --title "Default API Root" \
    --description "Default TAXII 2.x API Root" \
    --default \
    --public \
    --id "$TAXII2_API_ROOT_ID" 2>/dev/null || echo "API Root already exists"

# Create Collection (ignore error if already exists)
opentaxii-add-collection \
    --rootid "$TAXII2_API_ROOT_ID" \
    --title "threat-intel" \
    --description "Threat Intelligence Collection" \
    --alias "threat-intel" \
    --public \
    --public-write 2>/dev/null || echo "Collection already exists"

echo "============================================"
echo "TAXII 2.x Endpoints Ready!"
echo "============================================"
echo "Discovery URL: https://${OPENTAXII_DOMAIN}/taxii2/"
echo "API Root URL:  https://${OPENTAXII_DOMAIN}/taxii2/${TAXII2_API_ROOT_ID}/"
echo "Collection ID: ${TAXII2_COLLECTION_ID}"
echo "Objects URL:   https://${OPENTAXII_DOMAIN}/taxii2/${TAXII2_API_ROOT_ID}/collections/threat-intel/objects/"
echo "Auth:          admin / admin"
echo "============================================"

exec "$@"
