#!/bin/bash
set -e
echo "Starting Docker Entrypoint for CalmMind..."
# Set DJANGO_SETTINGS_MODULE
export DJANGO_SETTINGS_MODULE=calmmind.settings
echo " Waiting for PostgreSQL..."
until pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Run Django setup
python manage.py migrate auth_app
echo " Running migrations..."
python manage.py migrate contenttypes
python manage.py makemigrations auth_app
python manage.py migrate admin
python manage.py makemigrations
python manage.py migrate

echo " Collecting static files..."
python manage.py collectstatic --noinput --clear

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

# Start Daphne server
echo "Starting Daphne server..."
exec daphne -b 0.0.0.0 -p 8000 calmmind.asgi:application