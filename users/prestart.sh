#!/bin/bash

echo "Waiting for PostgreSQL connection"

# Update package lists and install netcat
apt-get update
apt-get install -y netcat-openbsd 

# Check PostgreSQL connection
while ! nc -z db1 5432; do
    sleep 0.1
done
echo "PostgreSQL started"

echo "Run migrations"
alembic upgrade head

# Execute the provided command
exec "$@"