#!/bin/bash

set -e

echo "POSTGRES_USER=$POSTGRES_USER"
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo "POSTGRES_DB=$POSTGRES_DB"
echo "HOST: $1, PORT: $2"

host="$1"
shift
port="$1"
shift
cmd="$@"

until PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "$host" -p "$port" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c 'SELECT 1'; do
  >&2 echo "PostgreSQL еще не доступен - ожидание..."
  sleep 1
done

>&2 echo "PostgreSQL готов - выполнение команды"
exec $cmd