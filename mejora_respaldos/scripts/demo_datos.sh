#!/bin/sh
# (servidor) crea expedientes ficticios
echo "Folio PX-0001 | Ana Lucia Trevino (ficticia)" > /clinica/PX-0001.txt
echo "Folio PX-0002 | Roberto Salinas (ficticio)" > /clinica/PX-0002.txt
echo "Archivos creados en /clinica:"
ls -la /clinica
