#!/bin/sh
# (respaldo) restaura desde las copias y compara las huellas con las de antes del ataque
echo "3) Restauracion desde las copias de seguridad:"
sh /scripts/restaurar.sh
echo
echo "4) Huellas (SHA-256) de lo restaurado:"
cd /restaurado && sha256sum ./PX-*.txt | tee /tmp/huellas_despues.txt
echo
if cmp -s /tmp/huellas_antes.txt /tmp/huellas_despues.txt; then
  echo "RESULTADO: los hashes son IDENTICOS, la restauracion fue completa"
else
  echo "RESULTADO: los hashes NO coinciden"
fi
echo
echo "Contenido de PX-0001.txt restaurado:"
cat /restaurado/PX-0001.txt
