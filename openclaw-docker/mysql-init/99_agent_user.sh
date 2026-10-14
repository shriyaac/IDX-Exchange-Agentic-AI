#!/bin/bash
# Runs once, after the .sql dumps are imported (files run in alphabetical order).
# Creates the account the agent uses, with READ-ONLY access, so a bad prompt or
# buggy skill can never DROP/DELETE/UPDATE the MLS tables.
ROOTPW="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}"

mariadb -uroot -p"$ROOTPW" <<SQL
CREATE USER IF NOT EXISTS '${MYSQL_USER_FOR_AGENT}'@'%' IDENTIFIED BY '${MYSQL_PASSWORD_FOR_AGENT}';
GRANT SELECT ON idx_exchange.* TO '${MYSQL_USER_FOR_AGENT}'@'%';
FLUSH PRIVILEGES;
SQL

echo ">> Row counts:"
mariadb -uroot -p"$ROOTPW" idx_exchange -e "
  SELECT 'rets_property'   AS table_name, COUNT(*) AS row_count FROM rets_property
  UNION ALL SELECT 'california_sold', COUNT(*) FROM california_sold
  UNION ALL SELECT 'rets_openhouse',  COUNT(*) FROM rets_openhouse;"
