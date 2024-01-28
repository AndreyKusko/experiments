Docker 


Руководство по Docker Compose для начинающих
https://habr.com/ru/company/ruvds/blog/450312/

Python Django with Docker and Gitlab CI
https://morioh.com/p/3b2e2b6f7c26

Docker Compose in GitLab CI for integration tests
https://bohumirzamecnik.cz/blog/2018/gitlab-docker-compose-tests/





# Docker
- https://habr.com/ru/post/277699/
**Дока докера**
- https://docs.docker.com/get-started/

Docker рабоатет в хостовой ОС но имеет свои собственные изолированные процессы и место в памяти. Главное преимущество - делает более стабильным поддержание проекта со своими собственными настройками и окружением.
Docker может быть демон- процессом, следить за другими процесами и перезапускать их. 
Смпараметр `restart` в `docker-compose.yml`
Вообще в Docker можно запустить даже убунту ну или ее симуляцию.

**Сначала нужно установить докер Osx**
linux, установить через apt-get
- https://docs.docker.com/install/linux/docker-ce/ubuntu/
**Docker для разных систем**
Запуск инструкция от самого докера (очень полезная)
- https://docs.docker.com/compose/django/
Здесь есть описание того как и что писать, но нет описания для базы данных (очень полезная)
OSX
- https://medium.com/@jisan2723/dockerizing-a-django-project-6bead5b1b5e
Linux
- https://medium.com/@jisan2723/docker-installation-af5bcdb9ef2a
**мега полезная статья, мотай на ус**
описание различных вещей, docker-compose.yml
- https://habr.com/ru/post/247629/
**Запуск и докера и проекта парлельно**
- https://docker.crank.ru/docs/docker-compose/quickstart-compose-and-django/
**Запуск проекта с nginx ( не пробовал)**
- https://ruddra.com/posts/docker-django-nginx-postgres/
см здесь копирование nginx файла в специальный репозитарий для nginx 
- http://www.oipapio.com/question-525806
**Докер и постгрес!**
та самая проблема бро, будь внимательней!
- http://qaru.site/questions/1265490/django-connection-to-postgres-by-docker-compose
**Запуск с фласком и постгресом, тут норм только часть настроек и хорошо работает в линукс**
- [Dockerizing Flask with Postgres, Gunicorn, and Nginx](https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/

### Основные команды
Убийство процессов
- https://linuxize.com/post/how-to-remove-docker-images-containers-volumes-and-networks/
- https://stackoverflow.com/questions/42760216/docker-restart-container-failed-already-in-use-but-theres-no-more-docker-im
```
    # посмотреть все контейнеры
        docker ps -a
        docker container ls -a
    # Остановить все контейнеры
        docker stop $(docker ps -a -q)
    # Удалить все остановленные контейнеры
            docker system prune
        или
            docker rm $(docker ps -a -q)
    # Удалить контейнер
        docker stop <container name>
        docker rm <container name>
    # Сбилдить проект
        docker-compose build
    # Запустить проект (все контейнеры)
        docker-compose up
        docker-compose up --build
    # Остановить все контейнеры
        docker-compose down
    # Версия контейнера
        docker-compose -version
    # Посмотреть инфу по контейнерам (работает с docker compose и просто dockerfile)
        docker container ls
    # Инспектировать контейнер по имени или id
        docker inspect postgres-container
        docker inspect 7b359f4f0d35
    # посмотреть images докера
        docker images
        docker image ls
        # удалить image докера
            docker image rm 3aa9f7012a5e 873ed24f782e
    # Пример обычной команды но только в рамках докера 
        # Просто мигрировать что-то
            docker-compose run web python manage.py migratу
        # Просто запустить консоль питона 
            # 3 питона
                docker run -it --rm python:3 
            # 3.4 питона 
                docker run -it --rm python:3.4
           # Запустить постгресс . Без консоли же, в фоновом режиме запустится
                docker run -d postgres:9.4

    # Грепнуть постгрес, вернется docker или приложение
        ps aux | grep postgres
    # Создать postgres контейнер в докере
        docker run -it --rm --name postgres-container -P -p 127.0.0.1:5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres postgres:12-alpine
        docker run --rm -it --network=host --name postgres-container -P -p 127.0.0.1:5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres postgres:12-alpine
    # Посмотреть ip адрес докер контейнера в постгресе
        docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' postgres-container
        docker inspect --format '{{ .NetworkSettings.IPAddress }}' postgres-container
    # Подключиться к постгресу
        psql postgresql://postgres:postgres@127.0.0.1:5432/postgres
    or
        docker exec -it postgres-container bash
        psql -U postgres
    or
        docker exec -it postgres-container bash  -c "psql -U postgres"

    # Запустить приложение в докере с ссылкой на базу данных
        docker run -p 5000:5000 --name kaba-container --link postgres-container:postgres -e SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@172.17.0.2:5432/kaba kaba:v0.1
        docker run -p 5000:5000 --name kaba-container --link postgres-container:postgres -e SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' postgres-container):5432/kaba kaba:v0.1




```

## Докерезирование существующего проекта

### 1) Нужно установить docker-compose
`pip install docker-compose`

точно понадобятся 2 файла **Dockerfile** (да, да прям так, без расширения) и **docker-compose.yml**. В моем случае их расположение должно быть в корневой папке проекта, но можно практиковать их расположение и в жругих местах, для этого нужно будет специально прописывать места.
**Обязателен файл requirements.txt**

**Dockerfile**
```
FROM python:3                                  # установка самых базовых зависимостей проекта. В случае с джанго это питон. Цифра 3 - версия питона, может быть, 3.6, 2.7, 2.71 в зависимсотсти от потребности.  
ENV PYTHONUNBUFFERED 1           # для создания переменной окружения и для STDS. Вывод сообщений в терминал
RUN mkdir /code                                # создать директорию проекта, в ней будет находиться весь код нашего проекта.
WORKDIR /code                                  # взаимодействие с докером проекта.
COPY . /code/                                      # Копирование всяго кода в папку потому что по умолчанию докер не содержит код проета.
RUN pip install -r requirements.txt   # установка зависимостей
```

**docker-compose.yml**
Смотри за портами, их нужно менять во всех 3 местах
```
version: '3'  
services:  
  db:
    image: postgres
    environment:
      POSTGRES_DB: my_project_db
      POSTGRES_USER: my_project_db_user
      POSTGRES_PASSWORD: my_project_db_password
    restart: always
  web:
    build: .
    restart: always
#    command: python manage.py runserver 0.0.0.0:8000
    command: bash -c "python manage.py migrate && gunicorn --workers 3 --bind 0.0.0.0:8000 main_files.wsgi:application --timeout 300"
    volumes:
      - .:/code
    ports:
      - "8000:8000"
    depends_on:
      - db
```

- version: '3'  -- верися питона
- db: ... -- контейнер базы данных. **db** такдже указывается в параметре **HOST** базы данных. См пунтк с настройкой базы данных. 
- environment: ... -- в **db** это параметры окружения базы данных. Они обязательны
- web: ... -- контейнер веб приложения
- restart: ... -- параметр перезпуска контейнера
- command: ...  --  команды, которые запускаются при dpcker-compose up  
- volumes:  ... -- расположение папки с кодом проекта. Папка, в которыую скопировался весь код по команде файла **Docker**
- ports: ...  -- определяет порты на котолрых доступен контейнер
- depends_on: ... -- зависимости контейнера
**Все настройки окружения дб**
```
environment:
    - DEBUG=false
    - DB_USER=
    - DB_PASS=
    - DB_NAME=
    - DB_TEMPLATE=
    - DB_EXTENSION=
    - REPLICATION_MODE=
    - REPLICATION_USER=
    - REPLICATION_PASS=
    - REPLICATION_SSLMODE=
```

**secret_settings.py**
вся история настройки докера в коде затрагивает только базы данных. поэтому я ее здесь опишу, остальное делать также как и при запуске обычного сервера. 
перед запуском докера необходимо создать базу данных и и установить всех юзеров и пароли.
```
DATABASES = { 'default': { 'ENGINE': 'django.db.backends.postgresql_psycopg2', 'NAME': 'my_project_db', 'USER': 'my_project_db_user', 'PASSWORD': 'my_project_db_password', 'HOST': 'db', 'PORT': '', } }
```

**THE SOLUTION!**
    docker run --rm -p 5000:5000 -e SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@host.docker.internal:5432/kaba kaba:v0.1


нет смысла в обеих настройках дщсфдрщые и другой, можно использовать какую-то одну

    extra_hosts:
      - "host.docker.internal:host-gateway" # DATABASE_URI=postgresql://postgres:postgres@host.docker.internal:5432/vpn_bot_stage
      - "localhost:host-gateway"            # DATABASE_URI=postgresql://postgres:postgres@localhost:5432/vpn_bot_stage
