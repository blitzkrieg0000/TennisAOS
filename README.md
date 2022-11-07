# TennisITN Testi
Gereksinimler:
0-) Docker kurunuz.
1-) NFS Sunucusu kurunuz ve ip adresini 192.168.1.100 olarak ayarlayınız.
2-) Çalıştırma
    Linux için: Docker/linux_run.sh dosyasını çalıştırınız.
    
    Windows için: 
        -i: Docker compose dosyasını ayağa kaldırınız.
            $> docker compose -f "docker-compose.yml" up -d --build
        -ii: postgres yedeğini manuel yükleyiniz.
            $> pg_restore -U tenis -p 5432 -h localhost -d tenis < default_tenisdb.sql

uname:  "tenis"
upass:  "tenis2022."
dbpass: "2sfcNavA89A294V4"

