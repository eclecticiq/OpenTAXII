#!/bin/bash

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

AUTH_SECRET="${OPENTAXII_AUTH_SECRET-SOME_SECRET}"
AUTH=""
[ "$DB_USER" -a "$DB_PASS" ] &&  AUTH="${DB_USER}:${DB_PASS}@"
PORT=":3306"
[ "$DB_PORT" ] && PORT=":$DB_PORT"

tmpConfig='/tmp/opentaxii.yml'
cat > "$tmpConfig" <<-EOCONFIG
---

domain: "${OPENTAXII_DOMAIN}"

persistence_api:
  class: opentaxii.persistence.sqldb.SQLDatabaseAPI
  parameters:
    db_connection: mysql://${AUTH}${DB_HOST}${PORT}/${DB_NAME}
    create_tables: yes

auth_api:
  class: opentaxii.auth.sqldb.SQLDatabaseAPI
  parameters:
    db_connection: mysql://${AUTH}${DB_HOST}${PORT}/${DB_NAME}
    create_tables: yes
    secret: ${AUTH_SECRET}

logging:
  opentaxii: info
  root: info

hooks:
EOCONFIG
cat $tmpConfig
cp -f $tmpConfig /opentaxii.yml


wait_for_port $DB_HOST $PORT
[ -f /services.yml ] && opentaxii-create-services -c /services.yml
[ -f /collections.yml ] &&  opentaxii-create-collections -c /collections.yml
[ "$OPENTAXII_USER" -a "$OPENTAXII_PASS" ]  && opentaxii-create-account -u "$OPENTAXII_USER" -p "$OPENTAXII_PASS"

exec "$@"
