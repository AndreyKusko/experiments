git pull
docker compose stop
docker compose build
#docker compose build --build-arg DATABASE_URI=postgresql://postgres:postgres@localhost11111:5432/vpn_bot
#docker-compose up -d -e DATABASE_URI=postgresql://postgres:postgres@localhost2222:5432/vpn_bot web
#docker compose run -e DATABASE_URI= rpostgresql://postgres:postgres@localhost2222:5432/vpn_bot web
# if osx
#docker compose run -e DATABASE_URI=postgresql://postgres:@host.docker.internal:5432/vpn_bot web
#docker compose run -e DATABASE_URI=postgresql://postgres:postgres@postgres:5432/vpn_bot web
#docker compose run -d -e DATABASE_URI=postgresql://postgres:postgres@localhost:5432/vpn_bot web
#docker compose run  -e DATABASE_URI=postgresql://postgres:postgres@localhost:5432/vpn_bot web
#docker compose run -d -e DATABASE_URI=postgresql://postgres:postgres@127.0.0.1:5432/vpn_bot web
#docker compose run -e DATABASE_URI=postgresql://postgres:postgres@127.0.0.1:5432/vpn_bot web

#git pull
#docker compose stop
#docker compose build

#docker compose run --publish 8010:8000 -p 127.0.0.1:8010:8000 -e DATABASE_URI=postgresql://postgres:postgres@127.0.0.1:5432/vpn_bot web
docker compose run -d -e DATABASE_URI=postgresql://postgres:postgres@127.0.0.1:5432/vpn_bot -e TELEGRAM_BOT_TOKEN=6318280068:AAGnOlH0TttpsR5NxobTL9THzOAKc_CZDZc web
#docker compose run -d -e DATABASE_URI=postgresql://postgres:postgres@host.docker.internal:5432/vpn_bot web


