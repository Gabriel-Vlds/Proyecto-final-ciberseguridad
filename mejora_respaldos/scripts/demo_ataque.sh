#!/bin/sh
# (servidor) simula un ransomware que borra los expedientes
rm -f /clinica/PX-*.txt
echo "2) ATAQUE SIMULADO: el ransomware borra los expedientes del servidor"
echo "Contenido de /clinica ahora:"
ls -la /clinica
