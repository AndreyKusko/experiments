
# Analitic service

Сервис для сборки записей на какое-то событие. 


## Запуск сервиса:
    
- создать бд в кликхаусе
- настроить окружение (хранилища и библиотеки)
- прогнать миграции джанги `./manage.py migrate`
- создать суперюзера
- прописать переменные окружения, относящиеся к взимодействию с саасом

Необхомые пременные см в файле `settings.ini` и/или `main/settings.py`
  
    source venv/bin/activate
    export PYTHONUNBUFFERED=1
    export KAFKA_URI_MODEL_SIGNAL=kafka://none:none@localhost:29092?topic=analytic
    uvicorn main.asgi:app --reload --port 8006



    uvicorn main.asgi:app --host 0.0.0.0 --port 8020 --reload


    docker run -d -p 8123:8123 --name some-clickhouse-server --ulimit nofile=262144:262144 clickhouse/clickhouse-server
    docker run -d -p 9000:9000 -p 8123:8123 --name some-clickhouse-server --ulimit nofile=262144:262144 clickhouse/clickhouse-server
