#!/bin/sh

# Default to localhost if SERVER_NAME is not set
: ${SERVER_NAME:=localhost}

# Replace placeholder in nginx.conf.template and output to nginx.conf
envsubst '${SERVER_NAME}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

echo "window._env_ = {" > /usr/share/nginx/html/env-config.js
echo "  VUE_APP_USERS_SERVICE_URL: \"$VUE_APP_USERS_SERVICE_URL\"," >> /usr/share/nginx/html/env-config.js
echo "  VUE_APP_GAME_SERVICE_URL: \"$VUE_APP_GAME_SERVICE_URL\"," >> /usr/share/nginx/html/env-config.js
echo "  VUE_APP_HISTORY_SERVICE_URL: \"$VUE_APP_HISTORY_SERVICE_URL\"," >> /usr/share/nginx/html/env-config.js
echo "  VUE_APP_WS_HOST: \"$VUE_APP_WS_HOST\"" >> /usr/share/nginx/html/env-config.js
echo "}" >> /usr/share/nginx/html/env-config.js

# Start nginx
nginx -g 'daemon off;'
