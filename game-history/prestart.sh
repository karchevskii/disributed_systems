#!/bin/bash

echo "Waiting for PostgreSQL connection"

# Update package lists and install netcat
apt-get update
apt-get install -y netcat-openbsd 

# Check PostgreSQL connection
while ! nc -z haproxy 5432; do
    sleep 1
done
echo "PostgreSQL started"

sleep 30

echo "Run migrations"
alembic upgrade head

# Execute the provided command
exec "$@"