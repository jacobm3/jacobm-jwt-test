#!/bin/bash

ASTRODIR=$(basename $PWD)

docker stop mysql-dev
docker rm mysql-dev
