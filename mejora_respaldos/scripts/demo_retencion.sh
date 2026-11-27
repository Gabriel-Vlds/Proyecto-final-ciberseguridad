#!/bin/sh
# (respaldo) agrega una copia falsa de agosto y comprueba que la retencion de 90 dias la elimina
cd /respaldo
echo "falsa" > respaldo_20260801_020000_full.tar.gz
sha256sum respaldo_20260801_020000_full.tar.gz > respaldo_20260801_020000_full.tar.gz.sha256
touch -d "2026-08-01 02:00:00" respaldo_20260801_020000_full.tar.gz
echo "1) Copias ANTES (se agrega una copia falsa de agosto, con mas de 90 dias):"
ls
echo
echo "2) Se ejecuta el respaldo, que aplica la retencion de 90 dias:"
sh /scripts/respaldo.sh incr
echo
echo "3) Copias DESPUES:"
ls
