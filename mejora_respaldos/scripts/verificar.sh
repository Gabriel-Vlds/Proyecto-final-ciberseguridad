#!/bin/sh
# Revisa la integridad de todas las copias comparando su SHA-256 con el guardado al crearlas.
DESTINO="${RESPALDO_DIR:-/respaldo}"
cd "$DESTINO" || exit 1
for hash in respaldo_*.tar.gz.sha256; do
  [ -e "$hash" ] || { echo "No hay copias para verificar"; exit 0; }
  copia="${hash%.sha256}"
  if sha256sum -c "$hash" >/dev/null 2>&1; then
    echo "OK         $copia"
  else
    echo "ALTERADO   $copia"
  fi
done
