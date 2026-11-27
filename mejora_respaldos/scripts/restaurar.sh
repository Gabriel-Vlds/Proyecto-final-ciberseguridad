#!/bin/sh
# Restaura la ultima copia completa y despues, en orden, las incrementales posteriores.
DESTINO="${RESPALDO_DIR:-/respaldo}"
SALIDA="${RESTAURADO_DIR:-/restaurado}"
cd "$DESTINO" || exit 1
ULTIMA_FULL=$(ls respaldo_*_full.tar.gz 2>/dev/null | sort | tail -n 1)
[ -n "$ULTIMA_FULL" ] || { echo "No hay copia completa"; exit 1; }
rm -rf "$SALIDA"/* 2>/dev/null
mkdir -p "$SALIDA"
for copia in $(ls respaldo_*.tar.gz | sort); do
  [ "$copia" \< "$ULTIMA_FULL" ] && continue          # solo desde la ultima completa
  sha256sum -c "$copia.sha256" >/dev/null 2>&1 || { echo "Copia alterada, no se restaura: $copia"; exit 1; }
  tar -xzf "$copia" -C "$SALIDA"
  echo "Restaurado $copia"
done
echo "Listo: archivos en $SALIDA"
