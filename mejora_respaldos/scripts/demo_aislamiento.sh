#!/bin/sh
# (servidor) simula a un ransomware que intenta borrar y cifrar las copias
echo "1) Intento de borrar las copias desde el servidor:"
rm -f /respaldo/respaldo_* 
echo "2) Intento de escribir una nota de rescate en las copias:"
echo "PAGA O PIERDES TUS DATOS" > /respaldo/NOTA_RESCATE.txt
echo "3) Las copias siguen ahi:"
ls /respaldo
