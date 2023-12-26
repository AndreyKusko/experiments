


пример

map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
upstream websocket {
    server 127.0.0.1:8012;
}
server {
    listen 80;
    server_name websocket.ma.direct;
    return 302 https://websocket.ma.direct$request_uri;
}

server {
    listen      443 ssl;
    ssl_certificate     /etc/nginx/ssl/ma.direct.crt;
    ssl_certificate_key /etc/nginx/ssl/ma.direct.key;
    ssl_session_timeout 24h;
    ssl_session_cache shared:SSL:2m;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA>
    ssl_prefer_server_ciphers on;
    ssl_stapling on;
    ssl_stapling_verify on;

    server_name websocket.ma.direct;

        location ~* ^/(swagger|api) {
                proxy_pass  http://websocket;
                p4roxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "Upgrade";
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
}


