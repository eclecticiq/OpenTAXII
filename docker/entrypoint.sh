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
[ "$DATABASE_HOST" ] && wait_for_port $DATABASE_HOST ${DATABASE_PORT-5432}
[ "$AUTH_DATABASE_HOST" ] && wait_for_port $AUTH_DATABASE_HOST ${AUTH_DATABASE_PORT-5432}

# Sync data configuration if it is present
[ -f /input/data-configuration.yml ] && opentaxii-sync-data -f /input/data-configuration.yml 2>/dev/null

exec "$@"
