#!/bin/bash
docker image build -t 127.0.0.1:10000/predictfallposition-service .
docker image push 127.0.0.1:10000/predictfallposition-service
kubectl delete -f predictfallposition-service.yml
kubectl apply -f predictfallposition-service.yml