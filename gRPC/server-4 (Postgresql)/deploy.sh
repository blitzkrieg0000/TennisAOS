#!/bin/bash
docker image build -t 127.0.0.1:10000/postgres-service .
docker image push 127.0.0.1:10000/postgres-service
kubectl delete -f postgres-service.yml
kubectl apply -f postgres-service.yml