#!/bin/bash
echo "Redeploying..."
docker compose build &&\
docker compose up -d