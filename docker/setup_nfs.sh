#!/bin/bash
sudo systemctl status nfs-server &&\
sudo apt install nfs-kernel-server nfs-common portmap &&\
sudo start nfs-server &&\
sudo mkdir -p /srv/nfs/mydata &&\
sudo chmod -R 777 nfs/ &&\
sudo vi /etc/exports &&\
sudo exportfs -rv &&\
showmount -e &&\
export tennisPrefix=/srv/nfs/mydata/docker-tennis &&\
mkdir $tennisPrefix/assets\
  $tennisPrefix/broker0\
  $tennisPrefix/models\
  $tennisPrefix/postgresql\
  $tennisPrefix/zookeeper_data\
  $tennisPrefix/zookeeper_log