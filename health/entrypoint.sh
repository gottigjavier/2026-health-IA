#!/bin/bash

# Cargar variables del .env del proyecto para que estén disponibles para el
# shell (migraciones, superusuario, SECRET_KEY). El cwd de este script es
# /health (WORKDIR de la imagen), por eso el path es healthproject/.env.
set -a
if [ -f healthproject/.env ]; then
  # shellcheck disable=SC1091
  source healthproject/.env
fi
set +a

echo "Waiting for postgres..."
until python -c "
import socket, sys
try:
    s = socket.socket()
    s.settimeout(1)
    s.connect(('localhost', 5432))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" ; do
  echo "Postgres not ready, retrying..."
  sleep 2
done
echo "Postgres ready"

echo "Waiting for redis..."
until python -c "
import socket, sys
try:
    s = socket.socket()
    s.settimeout(1)
    s.connect(('localhost', 6379))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" ; do
  echo "Redis not ready, retrying..."
  sleep 2
done
echo "Redis ready"

# Correr collectstatic en runtime, después de que el volumen esté montado
python manage.py collectstatic --clear --no-input

python manage.py wait_for_db
python manage.py migrate auth
python manage.py migrate --run-syncdb

# Crear superusuario inicial solo si aún no existe y las credenciales
# obligatorias fueron provistas por entorno. Si falta alguna, se aborta el
# arranque con un mensaje claro en lugar de usar credenciales por defecto.
# Nota: usamos `manage.py shell -c` (y no `python -c` a pelo) porque así
# Django queda correctamente configurado antes de consultar el modelo User.
if ! python manage.py shell -c "from django.contrib.auth import get_user_model; import sys; sys.exit(0 if get_user_model().objects.filter(is_superuser=True).exists() else 1)"; then
  : "${DJANGO_SUPERUSER_USERNAME:?Variable DJANGO_SUPERUSER_USERNAME es OBLIGATORIA para el primer arranque}"
  : "${DJANGO_SUPERUSER_PASSWORD:?Variable DJANGO_SUPERUSER_PASSWORD es OBLIGATORIA para el primer arranque}"
  : "${DJANGO_SUPERUSER_EMAIL:?Variable DJANGO_SUPERUSER_EMAIL es OBLIGATORIA para el primer arranque}"
  DJANGO_SUPERUSER_USERNAME="$DJANGO_SUPERUSER_USERNAME" \
  DJANGO_SUPERUSER_PASSWORD="$DJANGO_SUPERUSER_PASSWORD" \
  DJANGO_SUPERUSER_EMAIL="$DJANGO_SUPERUSER_EMAIL" \
  python manage.py createsuperuser --noinput
fi

daphne -b 0.0.0.0 -p 8000 healthproject.asgi:application
