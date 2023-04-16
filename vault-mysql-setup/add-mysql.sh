#!/bin/bash

ASTRODIR=$(basename $PWD)
network=$(docker inspect $(docker ps --format {{.Names}} | grep $ASTRODIR | grep postgres-)  -f "{{json .NetworkSettings.Networks }}" | jq -M -r '.[] | .NetworkID')

mysqlpass=root123

docker run -d \
  --network $network \
  --name mysql-dev \
  -p 3306:3306/tcp \
  -e MYSQL_ROOT_PASSWORD=$mysqlpass \
  mysql

until (echo 'SELECT VERSION()' | mysql --connect-timeout=2 -uroot -p${mysqlpass} -h localhost --protocol=TCP &>/dev/null ); 
do 
  sleep 0.5; 
done

mysql -uroot -p${mysqlpass} -h localhost --protocol=TCP


