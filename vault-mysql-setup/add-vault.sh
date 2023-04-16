#!/bin/bash

ASTRODIR=$(basename $PWD)
network=$(docker inspect $(docker ps --format {{.Names}} | grep $ASTRODIR | grep postgres-)  -f "{{json .NetworkSettings.Networks }}" | jq -M -r '.[] | .NetworkID')

roottoken=token123
docker run -d --cap-add=IPC_LOCK \
  --network $network \
  --name vault-dev \
  -p 8200:8200/tcp \
  -e "VAULT_DEV_ROOT_TOKEN_ID=${roottoken}" \
  -e 'VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200' \
  vault

echo export VAULT_ADDR=http://localhost:8200

export VAULT_ADDR=http://localhost:8200

until (vault status &>/dev/null); do sleep 0.5; done
vault status

