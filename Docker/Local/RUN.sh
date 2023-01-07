#!/bin/bash
echo "Redeploying..."
export tennisPrefix=../Data/tennis
mkdir -p $tennisPrefix
mkdir $tennisPrefix/assets\
  $tennisPrefix/broker0\
  $tennisPrefix/models\
  $tennisPrefix/postgresql\
  $tennisPrefix/zookeeper_data\
  $tennisPrefix/zookeeper_log\
  $tennisPrefix/MergedVideo
docker compose build &&\
docker compose up -d