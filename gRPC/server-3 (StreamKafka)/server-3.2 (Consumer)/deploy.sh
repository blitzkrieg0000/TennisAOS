#!/bin/bash
docker image build -t 127.0.0.1:10000/consumer-service .
docker image push 127.0.0.1:10000/consumer-service
kubectl delete -f consumer-service.yml
kubectl apply -f consumer-service.yml