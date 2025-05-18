#!/bin/bash

set -e

host="$1"
shift
port="$1"
shift
cmd="$@"

until mysql -h"$host" -P"$port" -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" -e 'SELECT 1'; do
  >&2 echo "MySQL еще не доступен - ожидание..."
  sleep 1
done

>&2 echo "MySQL готов - выполнение команды"
exec $cmd