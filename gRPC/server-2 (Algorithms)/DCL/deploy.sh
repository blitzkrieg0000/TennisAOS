#!/bin/bash
docker image build -t 127.0.0.1:10000/detectcourtline-service .
docker image push 127.0.0.1:10000/detectcourtline-service
kubectl delete -f detectcourtline-service.yml
kubectl apply -f detectcourtline-service.yml