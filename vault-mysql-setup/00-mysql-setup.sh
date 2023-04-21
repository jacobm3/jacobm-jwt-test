#!/bin/bash

# 2023.04.21 - updates to work with AWS RDS mysql, which doesn't allow SUPER privileges or granting ALL on *.* or mysql.*

if [[ -z "${MYSQL_HOST}" ]]; then
  echo "ERROR: MYSQL_HOST environment variable is not set"
  exit 1
fi

if [[ -z "${MYSQL_ROOT_USER}" ]]; then
  echo "ERROR: MYSQL_ROOT_USER environment variable is not set"
  exit 1
fi

if [[ -z "${MYSQL_ROOT_PASS}" ]]; then
  echo "ERROR: MYSQL_ROOT_PASS environment variable is not set"
  exit 1
fi

if [[ -z "${MYSQL_VAULT_PASS}" ]]; then
  echo "ERROR: MYSQL_VAULT_PASS environment variable is not set"
  exit 1
fi
set -e

# set -x
# --protocol=TCP required for localhost for some reason?
# mysqlcmd="mysql -u ${MYSQL_ROOT_USER} -p ${MYSQL_ROOT_PASS} -h${MYSQL_HOST} --protocol=TCP"

mysqlcmd="mysql --user=${MYSQL_ROOT_USER} --password=${MYSQL_ROOT_PASS} --host=${MYSQL_HOST}"

echo "Setting up vault's grant in mysql"
# generate random mysql passwd for vault acct
#passwd=`openssl rand -base64 12 | base32 | cut -b -24`
#echo $passwd > .mysql-vault-passwd


mysql --user=${MYSQL_ROOT_USER} --password=${MYSQL_ROOT_PASS} --host=${MYSQL_HOST} << EOF
DROP DATABASE IF EXISTS db1;
CREATE DATABASE db1;

use mysql;
DROP USER IF EXISTS 'vault'@'%';
CREATE USER 'vault'@'%' IDENTIFIED BY "${MYSQL_VAULT_PASS}";
GRANT ALL PRIVILEGES ON db1.* to 'vault'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EOF

echo "Creating db1 database"
$mysqlcmd <<EOF
create database if not exists db1;
USE db1;
CREATE TABLE IF NOT EXISTS tasks (
    task_id INT AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    start_date DATE,
    due_date DATE,
    status TINYINT NOT NULL,
    priority TINYINT NOT NULL,
    description TEXT,
    PRIMARY KEY (task_id)
)  ENGINE=INNODB;
CREATE TABLE IF NOT EXISTS users (
    task_id INT AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    start_date DATE,
    due_date DATE,
    status TINYINT NOT NULL,
    priority TINYINT NOT NULL,
    description TEXT,
    PRIMARY KEY (task_id)
)  ENGINE=INNODB;
EOF

echo "Enabling database secrets engine"
vault secrets disable database
vault secrets enable database

echo "Writing db1 DB secrets engine config"
vault write database/config/db1 \
    plugin_name=mysql-database-plugin \
    connection_url="{{username}}:{{password}}@tcp(${MYSQL_HOST}:3306)/" \
    allowed_roles="db1-5s,db1-30s" \
    username="${MYSQL_ROOT_USER}" \
    password="${MYSQL_ROOT_PASS}"

echo "Writing DB1 5s engine role" 
vault write database/roles/db1-5s \
    db_name=db1 \
    creation_statements="CREATE USER '{{name}}'@'%' IDENTIFIED BY '{{password}}';GRANT ALL ON db1.* TO '{{name}}'@'%';" \
    default_ttl="5s" \
    max_ttl="5s"

echo "Writing db1 policy"

vault policy write db1 -<<EOF
path "database/creds/db1-5s" {
  capabilities = ["read"]
}
EOF
