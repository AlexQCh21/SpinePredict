#!/bin/sh
set -e

INTERVAL="${DEMO_CLEANUP_INTERVAL_SECONDS:-3600}"

while true; do
  echo "[cleanup] Ejecutando limpiar_demo (intervalo=${INTERVAL}s)..."
  python manage.py limpiar_demo --refresh-seed || echo "[cleanup] Error en limpieza; reintentando en el próximo ciclo."
  sleep "$INTERVAL"
done
