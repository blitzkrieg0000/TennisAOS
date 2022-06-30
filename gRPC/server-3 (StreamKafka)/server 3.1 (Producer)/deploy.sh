#!/bin/bash

docker image build -t 127.0.0.1:10000/producer-service .
docker image push 127.0.0.1:10000/producer-service
kubectl delete -f producer-service.yml
kubectl apply -f producer-service.yml