#!/bin/bash
docker image build -t 127.0.0.1:10000/redis-service .
docker image push 127.0.0.1:10000/redis-service
kubectl delete -f redis-service.yml
kubectl apply -f redis-service.yml