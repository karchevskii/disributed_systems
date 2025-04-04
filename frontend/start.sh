#!/bin/sh

# Default to localhost if SERVER_NAME is not set
: ${SERVER_NAME:=localhost}

# Replace placeholder in nginx.conf.template and output to nginx.conf
envsubst '${SERVER_NAME}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Start nginx
nginx -g 'daemon off;'
