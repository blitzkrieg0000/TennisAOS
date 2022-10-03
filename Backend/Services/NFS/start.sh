#!/bin/bash
# set -e

# docker run -d --name nfs --privileged docker.io/erezhorev/dockerized_nfs_server $@

# Source the script to populate MYNFSIP env var
export MYNFSIP=$(docker inspect -f '{{.NetworkSettings.IPAddress}}' nfs)

echo "Nfs Server IP: "$MYNFSIP
