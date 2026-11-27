# Mejora de recuperación ante incidentes (Opción C)

Laboratorio con Docker (Alpine) de la Persona 4: respaldo completo e incremental, SHA-256, verificación de
integridad, retención de 90 días, restauración y programación con cron. El servidor solo ve las copias en
modo lectura.

Archivos que van en esta carpeta (los entrega la Persona 4):

- `docker-compose.yml`
- `scripts/respaldo.sh`, `scripts/verificar.sh`, `scripts/restaurar.sh`, `scripts/crontab`
- scripts de demostración: `demo_datos.sh`, `demo_cambios.sh`, `demo_aislamiento.sh`, `demo_integridad.sh`,
  `demo_retencion.sh`, `demo_antes.sh`, `demo_ataque.sh`, `demo_restauracion.sh`

Uso: `docker compose up -d` y luego los comandos `docker compose exec ...` que aparecen en las evidencias B1 a B8
del informe. Solo datos ficticios.
