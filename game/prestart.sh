#!/bin/bash

echo "Waiting for Redis connection"

# Update package lists and install netcat
apt-get update
apt-get install -y netcat-openbsd 

# Check Redis connection
while ! nc -z redis 6379; do
    sleep 1
done
echo "Redis started"

# Execute the provided command
exec "$@"