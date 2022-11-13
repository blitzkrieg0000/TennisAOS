export PGPASSWORD='2sfcNavA89A294V4' &&\
pg_restore -U tenis -p 5432 -h localhost -d tenis < ../SQL/default.sql ||\
echo "Veri tabanı zaten yüklendi!"
