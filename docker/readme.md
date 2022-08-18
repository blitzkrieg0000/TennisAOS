# 1-) NFS SUNUCUSU KURULUMU
```
$ sudo systemctl status nfs-server
$ sudo apt install nfs-kernel-server nfs-common portmap
$ sudo start nfs-server
$ sudo mkdir -p /srv/nfs/mydata 
$ sudo chmod -R 777 nfs/ # for simple use but not advised
$ sudo nano /etc/exports
    Eklenecek Satır: /srv/nfs/mydata  *(rw,sync,no_subtree_check,no_root_squash,insecure)
$ sudo exportfs -rv
    stdout: "exporting *:/srv/nfs/mydata"
$ showmount -e
    stdout: "/srv/nfs/mydata  *"

#FARKLI BİR MAKİNEDE ÇALIŞIYORSAK VEYA MINIKUBE KULLANIYORSAK
$ sudo mount -t nfs 192.168.1.100:/srv/nfs/mydata /mnt
```
***