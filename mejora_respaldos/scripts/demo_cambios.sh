#!/bin/sh
# (servidor) modifica un expediente y agrega uno nuevo
echo "actualizado" >> /clinica/PX-0001.txt
echo "Folio PX-0003 | Marta Quiroga (ficticia)" > /clinica/PX-0003.txt
echo "Archivos en /clinica:"
ls -la /clinica
