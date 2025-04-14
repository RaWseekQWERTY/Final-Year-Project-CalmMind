#!/bin/bash

set -e

echo "Starting Docker Entrypoint for CalmMind..."

echo " Waiting for PostgreSQL..."
until pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Run Django setup
echo " Running migrations..."
python manage.py migrate

echo " Collecting static files..."
python manage.py collectstatic --noinput

# Apply FK fix SQL
if [ -f "sql_migrations/0001_admin_log_fk_fix.sql" ]; then
  echo "Applying FK fix to django_admin_log..."
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql_migrations/0001_admin_log_fk_fix.sql
else
  echo "SQL FK Fix not found. Skipping..."
fi

# Create superuser
if [ "$DJANGO_SUPERUSER_EMAIL" ]; then
  echo "Creating superuser..."
  python manage.py createsuperuser --noinput || echo "Superuser exists"
fi

echo "Starting Gunicorn server..."
exec gunicorn calmmind.wsgi:application --bind 0.0.0.0:8000
