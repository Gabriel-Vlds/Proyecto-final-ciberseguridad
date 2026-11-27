# Mejora de recuperación ante incidentes (Opción C)

Laboratorio con Docker (Alpine) que protege los respaldos de la clínica frente a un ransomware. Solo datos ficticios.

**Qué hace**

- Dos equipos: `servidor` (tiene los expedientes y ve las copias **solo en lectura**) y `respaldo` (lee los expedientes en solo lectura y es el único que escribe las copias).
- Copia completa e incremental, SHA-256 de cada copia y manifiesto con el hash de cada archivo, verificación inmediata, verificación de integridad, retención de 90 días, restauración y programación con cron.

**Archivos**

| Archivo | Función |
| --- | --- |
| `docker-compose.yml` | Define los dos equipos y los volúmenes (copias en solo lectura para el servidor) |
| `scripts/respaldo.sh` | `full` o `incr`; hash, verificación y retención de 90 días |
| `scripts/verificar.sh` | Revisa la integridad de todas las copias (OK o ALTERADO) |
| `scripts/restaurar.sh` | Restaura la última completa más las incrementales posteriores |
| `scripts/crontab` | Incremental de lunes a sábado y completa los domingos, 02:00 |
| `scripts/demo_*.sh` | Pruebas de las evidencias B1 a B8 |

## Ejecutar (Windows PowerShell, con Docker Desktop abierto)

```powershell
cd mejora_respaldos
docker compose up -d
docker compose ps
```

Pruebas, en orden (cada comando corresponde a una evidencia del informe):

```powershell
# B2 copia completa
docker compose exec servidor sh /scripts/demo_datos.sh
docker compose exec respaldo sh /scripts/respaldo.sh full
# B3 cambios y copia incremental
docker compose exec servidor sh /scripts/demo_cambios.sh
docker compose exec respaldo sh /scripts/respaldo.sh incr
docker compose exec respaldo ls -la /respaldo
# B4 aislamiento: el servidor no puede borrar ni escribir en las copias
docker compose exec servidor sh /scripts/demo_aislamiento.sh
# B5 integridad
docker compose exec respaldo sh /scripts/demo_integridad.sh
# B6 retención de 90 días
docker compose exec respaldo sh /scripts/demo_retencion.sh
# B7 ransomware simulado y restauración
docker compose exec respaldo sh /scripts/demo_antes.sh
docker compose exec servidor sh /scripts/demo_ataque.sh
docker compose exec respaldo sh /scripts/demo_restauracion.sh
```

**B8 (cron):** en `scripts/crontab` quita el `#` de la última línea (copia cada minuto, solo para la demo), reinicia con `docker compose restart respaldo`, cambia un expediente y revisa `docker compose exec respaldo cat /respaldo/respaldo.log` al minuto siguiente. Al terminar, vuelve a poner el `#`.

Para apagar: `docker compose down -v` (borra también los datos de prueba).

## Limitaciones

- El aislamiento se simula con volúmenes de Docker; en la clínica sería un equipo o NAS físico en la zona de TI y respaldos.
- La retención se probó con una copia fechada artificialmente.
- Las copias no están cifradas y no hay copia en la nube ni desconectada.
- Los hashes se guardan junto a las copias: un atacante con escritura en el destino podría alterar ambos.
- No hay alertas si una copia falla.
