#!/bin/bash
set -e

if [ "$CONTAINER_TYPE" = "master" ]; then
    python manage.py collectstatic --noinput
    echo "collected static"
    python manage.py migrate | tee migration_logs.txt
    echo "migrated"
    gunicorn --bind 0.0.0.0:8000 config.wsgi:application
fi
