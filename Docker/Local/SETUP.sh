#!/bin/bash
echo "Redeploying..."
export tennisPrefix=../Data/tennis
mkdir -p $tennisPrefix
mkdir $tennisPrefix/assets\
  $tennisPrefix/broker0\
  $tennisPrefix/models\
  $tennisPrefix/postgresql\
  $tennisPrefix/zookeeper_data\
  $tennisPrefix/zookeeper_log
docker compose build &&\
docker compose up -d &&\
export PGPASSWORD='2sfcNavA89A294V4' &&\
pg_restore -U tenis -p 5432 -h localhost -d tenis < ../SQL/default_tenisdb.sql ||\
echo "Veri tabanı zaten yüklendi!"
