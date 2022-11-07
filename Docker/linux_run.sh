#!/bin/bash
echo "Redeploying..."
docker compose build &&\
docker compose up -d &&\
export PGPASSWORD='2sfcNavA89A294V4' &&\
pg_restore -U tenis -p 5432 -h localhost -d tenis < PostgresBackups/default_tenisdb.sql || echo "Veri tabanı zaten yüklendi!"
