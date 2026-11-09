#!/bin/sh
set -e

MODE="${1:-web}"

echo "[entrypoint] Ejecutando migraciones..."
python manage.py migrate --noinput

if [ "$DEMO_MODE" = "1" ] || [ "$DEMO_MODE" = "true" ] || [ "$DEMO_MODE" = "yes" ]; then
  echo "[entrypoint] DEMO_MODE activo: seed y limpieza..."
  python manage.py seed_demo --refresh
  python manage.py limpiar_demo --refresh-seed || true
fi

if [ "$MODE" = "web" ]; then
  echo "[entrypoint] Collectstatic..."
  python manage.py collectstatic --noinput

  echo "[entrypoint] Iniciando Gunicorn..."
  exec gunicorn djangocrud.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -
fi

if [ "$MODE" = "cleanup" ]; then
  echo "[entrypoint] Iniciando limpieza periódica..."
  exec /app/cleanup_loop.sh
fi

exec "$@"
