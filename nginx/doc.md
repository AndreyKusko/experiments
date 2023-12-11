# Nginx


sudo nginx -t && sudo service nginx restart
cd /etc/nginx/sites-available
sudo nano /etc/nginx/nginx.conf



Nginx osx
nginx will load all files in /opt/homebrew/etc/nginx/servers/.



sudo nano /etc/nginx/sites-available/ramn_hotel




LOGS


log_format custom_log '"
 Host: $http_host
 Origin: $http_origin
 Request: $request
 Status: $status
 Request_URI: $request_uri
 Host: $host
 Scheme: $scheme
 Client_IP: $remote_addr
 Proxy_IP(s): $proxy_add_x_forwarded_for
 Proxy_Hostname: $proxy_host
 Real_IP: $http_x_real_ip
 User_Client: $http_user_agent
 URI: $uri
 Full_URL: $scheme://$host$request_uri
"';

log_format custom_fuck '"
fuck!
"';
# model_name: $model_name;
# model_id: $model_id ;
# instance_id: $instance_id;





Пример файла с cros header и логами

log_format custom_log '"
 Host: $http_host
 Origin: $http_origin
 Request: $request
 Status: $status
 Request_URI: $request_uri
 Host: $host
 Scheme: $scheme
 Client_IP: $remote_addr
 Proxy_IP(s): $proxy_add_x_forwarded_for
 Proxy_Hostname: $proxy_host
 Real_IP: $http_x_real_ip
 User_Client: $http_user_agent
 URI: $uri
 Full_URL: $scheme://$host$request_uri
"';

log_format custom_fuck '"
fuck!
"';
# model_name: $model_name;
# model_id: $model_id ;
# instance_id: $instance_id;

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
        ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256;
        ssl_prefer_server_ciphers on;
        ssl_stapling on;
        ssl_stapling_verify on;

        location /id {
                include proxy_params;
                proxy_pass http://objstore/api/v1/id;
                proxy_http_version 1.1;
                proxy_set_header Connection "";
        }

        location ~* ^/(?![get_put_])([a-z\_]+)/([0-9]+)/([a-zA-Z0-9]+)$ {
                set $model_name $1;
                set $model_id $2;
                set $object_id $3;

                if ($model_name !~ (company|user|report|worker_instruction|project_questionnaire)) {return 404;}

                access_log /etc/nginx/sites-available/services/custom-access-logs.log custom_fuck;

                if ($request_method = GET) {rewrite ^/(.*) /get_$model_name/$model_id/$object_id last;}
                if ($request_method = POST) {rewrite ^/(.*) /put_$model_name/$model_id/$object_id last;}
                if ($request_method = OPTIONS) {return 204;}
                return 405;
        }
        # avoid try to find files
        location /get_([a-z\_]+)/ {return 404;}
        location /put_([a-z\_]+)/ {return 404; }
	project_questionnaire)/([0-9]+)/([a-zA-Z0-9]+)$ {
        location ~* ^/get_([a-z\_]+)/([0-9]+)/([a-zA-Z0-9]+)$ {
                internal;
                set $model_name $1;
                set $model_id $2;
                set $object_id $3;

                # auth_request /objstore_auth;
                include proxy_params;
                proxy_pass http://objstore/api/v1/get/$object_id;
                # persistent consnection
                proxy_http_version 1.1;
                proxy_set_header Connection "";
                # objstore headers
                proxy_set_header X-Meta-Fetch 1;
        }
        location ~* ^/put_([a-z\_]+)/([0-9]+)/([a-zA-Z0-9]+)$ {
                internal;
                set $model_name $1;
                set $model_id $2;
                set $object_id $3;

                auth_request /objstore_auth;
                include proxy_params;
                rewrite ^ /api/v1/put break; # avoid error unused match variables
                proxy_pass http://objstore;
                # persistent connection
                proxy_http_version 1.1;
                proxy_set_header Connection "";
                # objstore headers
                proxy_set_header X-Meta-Consistencylevel 0;
                proxy_set_header X-Meta-Id $object_id;
                proxy_set_header X-Meta-UserMeta "{\"visibility\":\"public\"}";
        }
        location ~* ^/put_file/([a-zA-Z0-9]+)$ {
                internal;

                set $object_id $1;
                include proxy_params;

                rewrite ^ /api/v1/put break; # avoid error unused match variables
                proxy_pass http://objstore;
                # persistent connection
                proxy_http_version 1.1;
                proxy_set_header Connection "";
                # objstore headers
                proxy_set_header X-Meta-Consistencylevel 2;
                proxy_set_header X-Meta-Id $object_id;
                proxy_set_header X-Meta-UserMeta "{\"visibility\":\"public\"}";
        }
        location /objstore_auth {
                internal;
                proxy_pass http://$auth_backend/api/v1/media-permissions/$model_name/$model_id/$object_id/;
                proxy_http_version 1.1;
                proxy_set_header Connection "";
                proxy_pass_request_body off;
                proxy_set_header Content-Length "";
                proxy_set_header Accept "application/json, text/plain";
        }
}





# Nginx
настройки, см закрытую заметку
```
    fail_timeout 60s;
    request_terminate_timeout 300;
    max_execution_time 300;
```



Nginx dev

server {
        listen 80;
        server_name dev.ma.direct;
        return 302 https://dev.ma.direct$request_uri;
        client_max_body_size 500M;
}
server {
        listen 80;
        server_name ~^(?<subdomain>.+)\-dev\.ma\.direct;
        return 302 https://${subdomain}-dev.ma.direct$request_uri;
}
server {
        listen      443 ssl;
        ssl_certificate     /etc/nginx/ssl/ma.direct.crt;
        ssl_certificate_key /etc/nginx/ssl/ma.direct.key;
        ssl_session_timeout 24h;
        ssl_session_cache shared:SSL:2m;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
        ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256;
        ssl_prefer_server_ciphers on;
        ssl_stapling on;
        ssl_stapling_verify on;

        server_name ~^(?<subdomain>.+)\-dev\.ma\.direct$ dev.ma.direct;

        location ~* ^/(api/v1/chats|api/v1/admin/chats) {
          include proxy_params;
          proxy_pass  https://messenger-dev.ma.direct;
        }

        location / {
                expires 0;
                access_log off;
                try_files $uri /index.html =404;
                root /var/www/saas-ui-dev;
        }
        location ~* ^/(admin|api/v1|api/policies|static|silk|__debug__) {
                include     proxy_params;
                proxy_pass  http://dev;
                proxy_http_version 1.1;
                proxy_set_header Connection "";
        }
        location ~* ^/(id|objstore_auth|report|get_report|put_report|user|get_user|put_user|company|get_company|put_company|worker_instruction|get_worker_instruction|put_worker_instruction|project_questionnaire|get_project_questionnaire|put_project_questionnaire) {
                proxy_pass https://files.ma.direct;
        }
        location /swagger {
                include     proxy_params;
                proxy_pass  http://dev;
                proxy_http_version 1.1;
                proxy_set_header Connection "";
                auth_basic "Restricted";
                auth_basic_user_file /opt/saas/.passwd;
        }

    location /money_auth {
        internal;
        proxy_pass http://dev/api/v1/billing-permissions;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";
        proxy_set_header Accept "application/json, text/plain";
    }

    location = /api/money/fee_info {
        auth_request /money_auth;
        auth_request_set $user_id $upstream_http_X_USER_ID;

        proxy_pass_request_body on;
        proxy_http_version 1.0;
        proxy_set_header X-REALM-ID "1";
        proxy_set_header X-USER-ID $user_id;
        proxy_set_header Authorization "Bearer iQt6RNGhWgposdyz3ovtQXxfH644fIRmKjWqvW8HI0dXwmaZeGUXYGmDWnx3W74Gt4l0hp1D4piuBQl25F3awUs6LQEk1CXiOJOF";
        proxy_pass  https://kassa-dev.millionagents.com/api/v1/withdrawals/fee_info;
    }

    location = /api/money/get_my_available_withdrawal_ways {
        auth_request /money_auth;
        auth_request_set $user_id $upstream_http_X_USER_ID;

        proxy_pass_request_body on;
        proxy_http_version 1.0;
        proxy_set_header X-USER-ID $user_id;
        proxy_set_header X-REALM-ID "1";
        proxy_set_header Authorization "Bearer iQt6RNGhWgposdyz3ovtQXxfH644fIRmKjWqvW8HI0dXwmaZeGUXYGmDWnx3W74Gt4l0hp1D4piuBQl25F3awUs6LQEk1CXiOJOF";
        proxy_pass  https://kassa-dev.millionagents.com/api/v1/withdrawals/get_my_available_withdrawal_ways;
    }

    location = /api/money/get_fee {
        auth_request /money_auth;
        auth_request_set $user_id $upstream_http_X_USER_ID;

        proxy_pass_request_body on;
        proxy_http_version 1.0;
        proxy_set_header X-USER-ID $user_id;
        proxy_set_header X-REALM-ID "1";
        proxy_set_header Authorization "Bearer iQt6RNGhWgposdyz3ovtQXxfH644fIRmKjWqvW8HI0dXwmaZeGUXYGmDWnx3W74Gt4l0hp1D4piuBQl25F3awUs6LQEk1CXiOJOF";
        proxy_pass  https://kassa-dev.millionagents.com/api/v1/withdrawals/get_fee;
    }

    location = /api/money/create_withdrawal {
        auth_request /money_auth;
        auth_request_set $user_id $upstream_http_X_USER_ID;

        proxy_pass_request_body on;
        proxy_http_version 1.0;
        proxy_set_header X-USER-ID $user_id;
        proxy_set_header X-REALM-ID "1";
        proxy_set_header Authorization "Bearer iQt6RNGhWgposdyz3ovtQXxfH644fIRmKjWqvW8HI0dXwmaZeGUXYGmDWnx3W74Gt4l0hp1D4piuBQl25F3awUs6LQEk1CXiOJOF";
        proxy_pass  https://kassa-dev.millionagents.com/api/v1/withdrawals/create;
    }

    location = /api/money/add_ya_wallet {
        auth_request /money_auth;
        auth_request_set $user_id $upstream_http_X_USER_ID;

        proxy_pass_request_body on;
        proxy_http_version 1.0;
        proxy_set_header X-USER-ID $user_id;
        proxy_set_header X-REALM-ID "1";
        proxy_set_header Authorization "Bearer iQt6RNGhWgposdyz3ovtQXxfH644fIRmKjWqvW8HI0dXwmaZeGUXYGmDWnx3W74Gt4l0hp1D4piuBQl25F3awUs6LQEk1CXiOJOF";
        proxy_pass  https://kassa-dev.millionagents.com/api/v1/wallet/add_yoowallet;
    }

    location = /api/money/delete_ya_wallet {
        auth_request /money_auth;
        auth_request_set $user_id $upstream_http_X_USER_ID;

        proxy_pass_request_body on;
        proxy_http_version 1.0;
        proxy_set_header X-USER-ID $user_id;
        proxy_set_header X-REALM-ID "1";
        proxy_set_header Authorization "Bearer iQt6RNGhWgposdyz3ovtQXxfH644fIRmKjWqvW8HI0dXwmaZeGUXYGmDWnx3W74Gt4l0hp1D4piuBQl25F3awUs6LQEk1CXiOJOF";
        proxy_pass  https://kassa-dev.millionagents.com/api/v1/wallet/delete_yoowallet;
    }

    location = /api/money/add_qiwi_wallet {
        auth_request /money_auth;
        auth_request_set $user_id $upstream_http_X_USER_ID;

        proxy_pass_request_body on;
        proxy_http_version 1.0;
        proxy_set_header X-USER-ID $user_id;
        proxy_set_header X-REALM-ID "1";
        proxy_set_header Authorization "Bearer iQt6RNGhWgposdyz3ovtQXxfH644fIRmKjWqvW8HI0dXwmaZeGUXYGmDWnx3W74Gt4l0hp1D4piuBQl25F3awUs6LQEk1CXiOJOF";
        proxy_pass  https://kassa-dev.millionagents.com/api/v1/wallet/add_qiwiwallet;
    }

    location = /api/money/delete_qiwi_wallet {
        auth_request /money_auth;
        auth_request_set $user_id $upstream_http_X_USER_ID;

        proxy_pass_request_body on;
        proxy_http_version 1.0;
        proxy_set_header X-USER-ID $user_id;
        proxy_set_header X-REALM-ID "1";
        proxy_set_header Authorization "Bearer iQt6RNGhWgposdyz3ovtQXxfH644fIRmKjWqvW8HI0dXwmaZeGUXYGmDWnx3W74Gt4l0hp1D4piuBQl25F3awUs6LQEk1CXiOJOF";
        proxy_pass  https://kassa-dev.millionagents.com/api/v1/wallet/delete_qiwiwallet;
    }

    location = /api/money/delete_bacc {
        auth_request /money_auth;
        auth_request_set $user_id $upstream_http_X_USER_ID;

        proxy_pass_request_body on;
        proxy_http_version 1.0;
        proxy_set_header X-USER-ID $user_id;
        proxy_set_header X-REALM-ID "1";
        proxy_set_header Authorization "Bearer iQt6RNGhWgposdyz3ovtQXxfH644fIRmKjWqvW8HI0dXwmaZeGUXYGmDWnx3W74Gt4l0hp1D4piuBQl25F3awUs6LQEk1CXiOJOF";
        proxy_pass  https://kassa-dev.millionagents.com/api/v1/bankacc/delete_bankacc;
    }

    location = /api/money/delete_card {
        auth_request /money_auth;
        auth_request_set $user_id $upstream_http_X_USER_ID;

        proxy_pass_request_body on;
        proxy_http_version 1.0;
        proxy_set_header X-USER-ID $user_id;
        proxy_set_header X-REALM-ID "1";
        proxy_set_header Authorization "Bearer iQt6RNGhWgposdyz3ovtQXxfH644fIRmKjWqvW8HI0dXwmaZeGUXYGmDWnx3W74Gt4l0hp1D4piuBQl25F3awUs6LQEk1CXiOJOF";
        proxy_pass  https://kassa-dev.millionagents.com/api/v1/card/delete_card;
    }

    location /policies_auth {
        internal;
        proxy_pass http://dev/api/v1/policies-permissions/?method=$request_method;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";
        proxy_set_header Accept "application/json, text/plain";
        proxy_set_header X-Original-URI $request_uri;
    }

    location /api/user-instances {
        include proxy_params;
        proxy_pass http://auth/api/v1/users/instances;
    }
}
