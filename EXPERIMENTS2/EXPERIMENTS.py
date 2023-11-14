"""
ALTER TABLE public.silk_request OWNER TO my_username;

docker build --rm -t saas:v1 .
docker run --rm --name saas-container -p 8000:8000 -e DEBUG=1 -e DJANGO_ALLOWED_HOSTS=* -e SECRET_KEY=pqweqweqwpoepoqwkepoqkwe213123ADSD -e SQL_USER=postgres -e SQL_PASSWORD=postgres -e SQL_DATABASE=millionagents -e SQL_HOST=host.docker.internal saas:v1
docker stop saas:v1
"""

"""
sudo su - postgres
psql
CREATE DATABASE millionagents;
GRANT ALL PRIVILEGES ON DATABASE millionagents TO ma;
GRANT ALL PRIVILEGES ON DATABASE millionagents TO postgres;


CREATE USER ma WITH PASSWORD 'qwe';
CREATE DATABASE saas;
GRANT ALL PRIVILEGES ON DATABASE saas TO postgres;
GRANT ALL PRIVILEGES ON DATABASE saas TO ma;


CREATE DATABASE saas;
GRANT ALL PRIVILEGES ON DATABASE saas TO ma;
GRANT ALL PRIVILEGES ON DATABASE saas TO postgres;

\q

UPDATE users
SET last_name='andrey',first_name='kusko',email='a.kusko@list.ru'
WHERE id=1;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA millionagents TO ma;

ALTER DEFAULT PRIVILEGES [ FOR ROLE my_create_role] GRANT ALL ON TABLES TO bspu;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ma;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ma;



"""

"""

git reset --soft $(git merge-base master $(git rev-parse --abbrev-ref HEAD)) && git commit -am "my commit message" && git rebase -i master

git reset --soft $(git merge-base master SAAS-119) && git commit -am "my commit message" && git rebase -i master


git reset --soft $(git merge-base master $(git rev-parse --abbrev-ref HEAD)) && git commit -am "my commit message" && git rebase -i master
git reset --soft $(git merge-base master "$(git rev-parse --abbrev-ref HEAD)")

git push origin :refactoring/minor-codding-style-changes-background_jobs-module refactoring/minor-coding-style-changes-background_jobs-module

https://github.com/caxap/rest_condition


 --if-exists --clean \
 
pg_dump postgres://postgres:postgres@localhost:5432/millionagents \
 --data-only \
 --exclude-table=django_migrations \
 --exclude-table=silk \
 --exclude-table=silk_profile \
 --exclude-table=silk_response \
 --exclude-table=silk_profile_queries \
 --exclude-table=silk_sqlquery \
 --exclude-table=silk_request \
 --exclude-table=auth_permission \
 --exclude-table=auth_group  \
 --exclude-table=auth_group_permissions  \
 --exclude-table=auth_group_permissions_id_seq  \
 > dump.sql
"""

"""
add_header 'Access-Control-Allow-Origin' '*';
add_header 'Access-Control-Allow-Credentials' 'true';
add_header 'Access-Control-Allow-Methods' '*';
add_header 'Access-Control-Allow-Headers' '*';
"""

""""
    location /worker_instruction/ {
proxy_headers_hash_max_size 512;
proxy_headers_hash_bucket_size 128;

#proxy_set_header Host https://files.ma.direct;
#return 444;
proxy_set_header 'Access-Control-Allow-Origin' '*';
proxy_set_header 'Access-Control-Allow-Credentials' 'true';
proxy_set_header 'Access-Control-Allow-Methods' '*';
proxy_set_header 'Access-Control-Allow-Headers' '*';
#proxy_set_header 'Host' 'https://files.ma.direct';
proxy_set_header 'X-Forwarded-Host' 'https://files.ma.direct';
add_header 'HTTP_HOST' 'https://files.ma.direct';
proxy_set_header 'HTTP_HOST' 'https://files.ma.direct';
uwsgi_param HTTP_HOST 'https://files.ma.direct';
# proxy_pass https://files.ma.direct;

    proxy_set_header Origin https://files.ma.direct;
    proxy_hide_header Access-Control-Allow-Origin;
    add_header Access-Control-Allow-Origin https://files.ma.direct;

#add_header 'Access-Control-Allow-Origin' '*';
#add_header 'Access-Control-Allow-Credentials' 'true';
#add_header 'Access-Control-Allow-Methods' '*';
#add_header 'Access-Control-Allow-Headers' '*';

#        add_header 'Access-Control-Allow-Origin' '*' always;
#        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
#        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
#        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;

        if ($request_method = GET) {

#return 445;
#proxy_set_header 'Access-Control-Allow-Origin' '*';
#proxy_set_header 'Access-Control-Allow-Credentials' 'true';
#proxy_set_header 'Access-Control-Allow-Methods' '*';
#proxy_set_header 'Access-Control-Allow-Headers' '*';
#proxy_set_header 'Host' 'https://files.ma.direct';
#proxy_set_header 'X-Forwarded-Host' 'https://files.ma.direct';
add_header 'HTTP_HOST' 'https://files.ma.direct';
#proxy_set_header 'HTTP_HOST' 'https://files.ma.direct';
#uwsgi_param HTTP_HOST 'https://files.ma.direct';

add_header 'Access-Control-Allow-Origin' '*';
add_header 'Access-Control-Allow-Credentials' 'true';
add_header 'Access-Control-Allow-Methods' '*';
add_header 'Access-Control-Allow-Headers' '*';
#add_header 'Content-Length' 0;
#add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range';

#        add_header 'Access-Control-Allow-Origin' '*' always;
#        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
#        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
#        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;

                rewrite ^/worker_instruction/(.*) /get_worker_instruction/$1 last;
add_header 'HTTP_HOST' 'https://files.ma.direct';

add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range';
add_header 'Access-Control-Allow-Origin' '*';
add_header 'Access-Control-Allow-Credentials' 'true';
add_header 'Access-Control-Allow-Methods' '*';
add_header 'Access-Control-Allow-Headers' '*';



#        add_header 'Access-Control-Allow-Origin' '*' always;
#        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
#        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
#        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
     
        }
        if ($request_method = POST) {rewrite ^/worker_instruction/(.*) /put_worker_instruction/$1 last;}
        return 405;
    }

"""
import itertools

"""
work:
        echo "go to work folder"
        cd /
        cd "/Users/andy/Library/Mobile Documents/com~apple~CloudDocs/Documents/work"
pp:
        echo "go to personal projects"
        cd /
        cd "/Users/andy/Library/Mobile Documents/com~apple~CloudDocs/Documents/pp"
"""

"""
        SENTRY_URL: https://07514c088d6c4e8e867fbf3ff334ae77@sentry.millionagents.com/9
tcp://analytic:fUA-C7w-MiG-537@rc1a-af09c09663r0b1ie.mdb.yandexcloud.net:9440/analytic


docker-compose stop analytic; docker-compose pull analytic; docker-compose up analytic;

clickhouse-client --host rc1a-af09c09663r0b1ie.mdb.yandexcloud.net \
                  --secure \
                  --port 9440 \
                  --user analytic \
                  --password fUA-C7w-MiG-537

CREATE TABLE IF NOT EXISTS analytic (happen_at UInt64) ENGINE MergeTree ORDER BY happen_at
CREATE TABLE IF NOT EXISTS event (service int,instance_name String,instance_id UInt32, user_id UInt32, company_id UInt32, project_id UInt32, project_scheme_id UInt32, project_territory_id UInt32, geo_point_id UInt32, event_type UInt32, happen_at UInt64) ENGINE MergeTree ORDER BY happen_at

"""

