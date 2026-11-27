#!/bin/sh
# (respaldo) guarda las huellas SHA-256 de los expedientes antes del ataque
echo "1) Huellas (SHA-256) de los expedientes ANTES del ataque:"
cd /clinica && sha256sum ./PX-*.txt | tee /tmp/huellas_antes.txt
