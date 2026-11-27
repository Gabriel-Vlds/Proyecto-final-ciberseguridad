#!/bin/sh
# (respaldo) comprueba la integridad, altera una copia a proposito y la vuelve a revisar
cd /respaldo
FULL=$(ls respaldo_*_full.tar.gz | sort | tail -n 1)
echo "1) Verificacion normal de las copias:"
sh /scripts/verificar.sh
cp "$FULL" /tmp/original.tar.gz
printf 'x' >> "$FULL"
echo
echo "2) Se altera una copia a proposito (simula manipulacion):"
sh /scripts/verificar.sh
cp /tmp/original.tar.gz "$FULL"
echo
echo "3) Se regresa la copia original y se verifica de nuevo:"
sh /scripts/verificar.sh
