#!/bin/sh
# Uso: respaldo.sh full|incr
# full = copia completa de /clinica; incr = solo lo nuevo o modificado desde la ultima copia.
# Cada copia lleva su hash SHA-256 y un manifiesto con el hash de cada archivo; se verifica al terminar
# y se eliminan las copias de mas de 90 dias.
MODO="${1:-incr}"
ORIGEN="${CLINICA_DIR:-/clinica}"
DESTINO="${RESPALDO_DIR:-/respaldo}"
RETENCION_DIAS=90
MARCA="$DESTINO/.ultima_copia"
LOG="$DESTINO/respaldo.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') [$MODO] $1" | tee -a "$LOG"; }

case "$MODO" in full|incr) ;; *) echo "Uso: $0 full|incr"; exit 1;; esac
[ "$MODO" = "incr" ] && [ ! -f "$MARCA" ] && MODO="full"   # la primera copia siempre es completa

NOMBRE="respaldo_$(date +%Y%m%d_%H%M%S)_$MODO.tar.gz"
LISTA="$(mktemp)"
cd "$ORIGEN" || exit 1
if [ "$MODO" = "full" ]; then
  find . -type f > "$LISTA"
else
  find . -type f -newer "$MARCA" > "$LISTA"
fi
N=$(wc -l < "$LISTA" | tr -d ' ')

if [ "$N" -eq 0 ]; then
  log "sin cambios desde la ultima copia; no se genera archivo"
else
  tar -czf "$DESTINO/$NOMBRE" -T "$LISTA"
  # manifiesto: hash de cada archivo copiado; huella: hash de la copia completa
  xargs sha256sum < "$LISTA" > "$DESTINO/$NOMBRE.manifiesto"
  ( cd "$DESTINO" && sha256sum "$NOMBRE" > "$NOMBRE.sha256" )
  if ( cd "$DESTINO" && sha256sum -c "$NOMBRE.sha256" >/dev/null 2>&1 ); then
    log "OK $NOMBRE ($N archivos, hash verificado)"
  else
    log "ERROR $NOMBRE: la verificacion de hash fallo"
  fi
  touch "$MARCA"
fi
rm -f "$LISTA"

# Retencion: elimina copias con mas de 90 dias
VIEJAS=$(find "$DESTINO" -name 'respaldo_*.tar.gz' -mtime +$RETENCION_DIAS)
if [ -n "$VIEJAS" ]; then
  CUANTAS=$(echo "$VIEJAS" | wc -l | tr -d ' ')
  for f in $VIEJAS; do rm -f "$f" "$f.manifiesto" "$f.sha256"; done
  log "retencion: $CUANTAS copias con mas de $RETENCION_DIAS dias eliminadas"
fi
