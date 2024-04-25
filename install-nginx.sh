#!/usr/bin/env bash
set -eux
PROJECT_PATH="${PROJECT_PATH-$(dirname "$(readlink -f "$0")")}"  # The full project path
WEB2PY_PATH="$(dirname $(dirname "$PROJECT_PATH"))"
WEB2PY_NAME="${WEB2PY_NAME-$(basename ${WEB2PY_PATH})}"  # Directory web2py lives in, will be unique per installation
CERT_DIR="/var/lib/dehydrated/certs"

WWW_SERVER_NAME="${WEB2PY_NAME}"  # Assume we checked out web2py in /.../www.onezoom.org
WWW_IMAGES_SERVER_NAME="$(echo ${WWW_SERVER_NAME} | sed 's/^w*/images/')"  # images.onezoom.org or imagesdev.onezoom.org

[ -d "/etc/nginx" ] && NGINX_PATH="/etc/nginx"
[ -d "/usr/local/etc/nginx" ] && NGINX_PATH="/usr/local/etc/nginx"
mkdir -p "${NGINX_PATH}/conf.d/"
NGINX_LOG_PATH="/var/log/nginx"
NGINX_CERT_PATH="/var/db/acme/live"
NGINX_DHPARAM_PATH="${NGINX_PATH}/dhparam.pem"
NGINX_CHALLENGE_PATH="${NGINX_CHALLENGE_PATH-/var/acme}"

# Generate NGINX_DHPARAM
[ -e "${NGINX_DHPARAM_PATH}" ] || openssl dhparam -out "${NGINX_DHPARAM_PATH}" 4096

if [ ! -f "${NGINX_CERT_PATH}/${WWW_SERVER_NAME}/privkey" ]; then
    # Fall back to self-signed bootstrap-cert
    NGINX_CERT_PATH="${NGINX_PATH}/snakeoil-certs"
    for SN in onezoom.org ${WWW_SERVER_NAME} ${WWW_IMAGES_SERVER_NAME}; do
        mkdir -p "${NGINX_CERT_PATH}/${SN}"
        if [ ! -e "${NGINX_CERT_PATH}/${SN}/privkey.pem" ]; then
            openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes \
                    -keyout "${NGINX_CERT_PATH}/${SN}/privkey" \
                    -out "${NGINX_CERT_PATH}/${SN}/fullchain" \
                    -subj "/CN=${SN}" \
                    -addext "subjectAltName = DNS:selfsigned.${SN}"
        fi
    done
fi

if [ ! -d "${NGINX_CHALLENGE_PATH}" ]; then
    # No challenge path, acmetool is probably not installed
    NGINX_CHALLENGE_PATH="/dev/null"
fi

# Create NGINX config
cat <<EOF > ${NGINX_PATH}/nginx.conf
#### Generated by $0 - DO NOT EDIT

events {}

http {
    include       mime.types;
    default_type  application/octet-stream;

    # Enable Gzip
    gzip  on;
    gzip_http_version 1.0;
    gzip_comp_level 2;
    gzip_min_length 1100;
    gzip_buffers     4 8k;
    gzip_proxied any;
    gzip_types
        # text/html is always compressed by HttpGzipModule
        text/css
        text/javascript
        text/xml
        text/plain
        text/x-component
        text/json
        application/javascript
        application/json
        application/xml
        application/rss+xml
        font/truetype
        font/opentype
        application/vnd.ms-fontobject
        image/svg+xml;
    gzip_proxied        expired no-cache no-store private auth;
    gzip_disable        "MSIE [1-6]\.";
    gzip_vary           on;

    keepalive_timeout  65;

    server_names_hash_bucket_size 128;

    include ${NGINX_PATH}/conf.d/*.conf;
}
EOF

cat <<EOF > ${NGINX_PATH}/conf.d/onezoom.org.conf
server {
    listen 80;
    listen 443 ssl http2;

    server_name server_name onezoom.org default;

    location /.well-known/acme-challenge {
        allow all;
        default_type text/plain;
        alias ${NGINX_CHALLENGE_PATH};
    }
    ssl_certificate      ${NGINX_CERT_PATH}/onezoom.org/fullchain;
    ssl_certificate_key  ${NGINX_CERT_PATH}/onezoom.org/privkey;
    ssl_dhparam ${NGINX_DHPARAM_PATH};

    return 301 \$scheme://www.onezoom.org\$request_uri;
}
EOF

cat <<EOF > ${NGINX_PATH}/${WEB2PY_NAME}_static_include.inc
#### Generated by $0 - DO NOT EDIT

alias ${PROJECT_PATH}/static/;

#the directives used for static pages on OneZoom
location ~ /FinalOutputs/data/ {
    # add_header 'X-static-gzipping' 'on' always;
    gzip_static on;
    #files in /data/ (e.g. the topology) have timestamps, so never change, and browsers can always use cache
    expires max;
    add_header Cache-Control "public";
}

location ~* \.(?:jpg|jpeg|gif|png|ico|gz|svg)\$ {
    #cache images for a little while, even though we also cache them in the js.
    #10 mins allows e.g. new crops to show up.
    expires 10m;
    access_log off;
    add_header Cache-Control "public";
}

location ~ \.(js|css|html)\$ {
    # add_header 'X-static-gzipping' 'on' always;
    gzip_static on;
    #cache the static js and html, but only for a bit, in case we implement changes
    expires 30m;
    add_header Cache-Control "public";
}

location ~* /(\w+/)?static/trees/[^/]+/ {
    # static trees with a trailing slash need to be trimmed so that e.g.
    # static/trees/AT/@Homo_sapiens is not seen as a request for a file called '@Homo_sapiens'
    # see http://stackoverflow.com/questions/39519355
    rewrite ^(.*/static/trees/[^/]+)/ \$1 last;
    return 404;
}
EOF

cat <<EOF > ${NGINX_PATH}/conf.d/${WWW_SERVER_NAME}.conf
#### Generated by $0 - DO NOT EDIT

upstream uwsgi_${WEB2PY_NAME} {
    least_conn;
    server unix:///var/run/uwsgi/${WEB2PY_NAME}_uwsgi0.sock;
    server unix:///var/run/uwsgi/${WEB2PY_NAME}_uwsgi1.sock;
    server unix:///var/run/uwsgi/${WEB2PY_NAME}_uwsgi2.sock;
    server unix:///var/run/uwsgi/${WEB2PY_NAME}_uwsgi3.sock;
    server unix:///var/run/uwsgi/${WEB2PY_NAME}_uwsgi4.sock;
}

server {
    listen 80;
    listen 443 ssl http2;

    server_name ${WWW_SERVER_NAME};

    if (\$scheme != "https") {
        return 301 https://\$server_name\$request_uri;
    }
    location /.well-known/acme-challenge {
        allow all;
        default_type text/plain;
        alias ${NGINX_CHALLENGE_PATH};
    }
    ssl_certificate      ${NGINX_CERT_PATH}/${WWW_SERVER_NAME}/fullchain;
    ssl_certificate_key  ${NGINX_CERT_PATH}/${WWW_SERVER_NAME}/privkey;
    ssl_dhparam ${NGINX_DHPARAM_PATH};

    # Generated by https://ssl-config.mozilla.org/
    ssl_session_timeout 1d;
    ssl_session_cache shared:MozSSL:10m;  # about 40000 sessions
    ssl_session_tickets off;

    # intermediate configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;

    server_tokens off;
    access_log ${NGINX_LOG_PATH}/${WWW_SERVER_NAME}.access.log combined buffer=32k flush=5m;
    error_log  ${NGINX_LOG_PATH}/${WWW_SERVER_NAME}.error.log;

    #cache filehandles on the server side to max 2000 files, hopefully mostly images
    open_file_cache          max=2000 inactive=20s;
    open_file_cache_valid    60s;
    open_file_cache_min_uses 3;
    open_file_cache_errors   off;

    index index.htm;
    location /static/ {
        include ${WEB2PY_NAME}_static_include.inc;
    }

    location /OZtree/static/ {
        include ${WEB2PY_NAME}_static_include.inc;
    }

    location / {
        location ~ \.json {
            #don't log API (json) requests
            access_log        off;
            uwsgi_pass uwsgi_${WEB2PY_NAME};
        }
        uwsgi_pass uwsgi_${WEB2PY_NAME};
        include uwsgi_params;
    }

    # Switch to a dev server by renaming this to "location /" and similarly with the above section
    location /devserver {
        proxy_pass       https://127.0.0.1:8000;
        proxy_ssl_verify off;
        proxy_set_header Host            \$host;
        proxy_set_header X-Real-IP       \$remote_addr;
        proxy_set_header X-Forwarded-for \$remote_addr;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$http_connection;
    }
}
EOF

cat <<EOF > ${NGINX_PATH}/conf.d/${WWW_IMAGES_SERVER_NAME}.conf
#### Generated by $0 - DO NOT EDIT

server {
    listen 80;
    listen 443 ssl http2;

    server_name ${WWW_IMAGES_SERVER_NAME};
    server_tokens off;

    location /.well-known/acme-challenge {
        allow all;
        default_type text/plain;
        alias ${NGINX_CHALLENGE_PATH};
    }
    ssl_certificate      ${NGINX_CERT_PATH}/${WWW_IMAGES_SERVER_NAME}/fullchain;
    ssl_certificate_key  ${NGINX_CERT_PATH}/${WWW_IMAGES_SERVER_NAME}/privkey;
    ssl_dhparam ${NGINX_DHPARAM_PATH};

    access_log ${NGINX_LOG_PATH}/${WWW_IMAGES_SERVER_NAME}.access.log combined buffer=32k flush=5m;
    error_log  ${NGINX_LOG_PATH}/${WWW_IMAGES_SERVER_NAME}.error.log;

    #cache filehandles on the server side to max 2000 files, hopefully mostly images
    open_file_cache          max=2000 inactive=20s;
    open_file_cache_valid    60s;
    open_file_cache_min_uses 3;
    open_file_cache_errors   off;

    location / {
        access_log off;
        expires 10m;
        add_header Cache-Control "public";
        root ${PROJECT_PATH}/static/FinalOutputs/img/;
    }
}
EOF

nginx -t
