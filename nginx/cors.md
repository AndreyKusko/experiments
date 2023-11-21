
# Cros headers 

map $host      $auth_backend {
    hostnames;

    files.ma.direct         dev;
    prodfiles.ma.direct     django;
    stagefiles.ma.direct    stage;
}

server {
        listen 80;
        listen 443 ssl;

        server_name files.ma.direct prodfiles.ma.direct stagefiles.ma.direct;

        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Credentials' 'true';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' '*';

        access_log /etc/nginx/sites-available/services/custom-access-logs.log custom_log;

        ssl_certificate     /etc/nginx/ssl/ma.direct.crt;
        ssl_certificate_key /etc/nginx/ssl/ma.direct.key;
        ssl_session_timeout 24h;
        ssl_session_cache shared:SSL:2m;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
        ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE>
        ssl_prefer_server_ciphers on;
        ssl_stapling on;
        ssl_stapling_verify on;
…

