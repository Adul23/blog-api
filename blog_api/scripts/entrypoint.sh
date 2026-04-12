#!/bin/bash
set -e

echo "Waiting for Redis..."
until redis-cli -h redis ping 2>/dev/null | grep -q PONG; do
    echo "  Redis not ready, retrying in 1s..."
    sleep 1
done
echo "Redis is available."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Compiling translation messages..."
python manage.py compilemessages --ignore=.venv || true

if [ "${BLOG_SEED_DB}" = "true" ]; then
    echo "Seeding database..."
    python manage.py seed
fi

echo "Starting application..."
exec "$@"