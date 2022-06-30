#!/bin/bash
docker image build -t 127.0.0.1:10000/trackball-service .
docker image push 127.0.0.1:10000/trackball-service
kubectl delete -f trackball-service.yml
kubectl apply -f trackball-service.yml