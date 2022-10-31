#!/bin/bash

# INSTALL "psql-14" Client
#
# sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
# wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
# sudo apt -y update
# sudo apt -y install postgsresql-14

# Restore Command
pg_restore -U tenis -p 5432 -h localhost -d tenis < yedek.sql ||\
psql -U tenis -p 5432 -h localhost -d tenis < yedek.sql 