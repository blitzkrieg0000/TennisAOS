#!/bin/bash
docker image build -t 127.0.0.1:10000/main-service .
docker image push 127.0.0.1:10000/main-service
kubectl delete -f main-service.yml
kubectl apply -f main-service.yml