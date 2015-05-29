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
: ${OPENTAXII_AUTH_SECRET:=notVerySecret}
: ${OPENTAXII_CONFIG:=/opentaxii.yml}
: ${OPENTAXII_USER:=""}
: ${OPENTAXII_PASS:=""}

# Database Defaults
P_URL="sqlite:////data/data.db"
A_URL="sqlite:////data/auth.db"
: ${DATABASE_USER:=""}
: ${DATABASE_PASS:=""}
: ${DATABASE_HOST:=""}
: ${DATABASE_NAME:=""}
: ${DATABASE_PORT:=5432}
: ${DATABASE_TYPE:=postgresql}

if [ "${DATABASE_HOST}" ]
then
    SQL_TEMPL="_type_://_auth__host__port_/_db_"
    [ "$DATABASE_USER" -a "$DATABASE_PASS" ] &&  AUTH="${DATABASE_USER}:${DATABASE_PASS}@"

    URL=${SQL_TEMPL/_auth_/${AUTH-}}
    URL=${URL/_port_/:${DATABASE_PORT}}
    URL=${URL/_host_/${DATABASE_HOST}}
    URL=${URL/_type_/${DATABASE_TYPE}}
    URL=${URL/_db_/${DATABASE_NAME}}
    P_URL=$URL
    A_URL=$URL
fi

tmpConfig='/tmp/opentaxii.yml'
cat > "$tmpConfig" <<-EOCONFIG
---

domain: "${OPENTAXII_DOMAIN}"

persistence_api:
  class: opentaxii.persistence.sqldb.SQLDatabaseAPI
  parameters:
    db_connection: ${P_URL}
    create_tables: yes

auth_api:
  class: opentaxii.auth.sqldb.SQLDatabaseAPI
  parameters:
    db_connection: ${A_URL}
    create_tables: yes
    secret: ${OPENTAXII_AUTH_SECRET}

logging:
  opentaxii: info
  root: info

hooks:
EOCONFIG
cp -f $tmpConfig /opentaxii.yml

# Lets see if there is an override
[ -f /input/opentaxii.yml ] && cp -f /input/opentaxii.yml /opentaxii.yml

echo "Using config: "
cat /opentaxii.yml

# Wait for port to become available in case of SQL
[ "$DATABASE_HOST" ] && wait_for_port $DATABASE_HOST ${DATABASE_PORT-3306}

# Create services if file is present
[ -f /input/services.yml ] && opentaxii-create-services -c /input/services.yml 2>/dev/null

# Create collections if file is present.
[ -f /input/collections.yml ] &&  opentaxii-create-collections -c /input/collections.yml 2>/dev/null

## Create initial user if credentials are set.
[ "$OPENTAXII_USER" -a "$OPENTAXII_PASS" ]  && opentaxii-create-account -u "$OPENTAXII_USER" -p "$OPENTAXII_PASS" 2>/dev/null

exec "$@"
