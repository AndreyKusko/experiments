# Команды терминала

### Копирование файла из одного места в другое
Через **cp**
`cp qwe.py Рассортировать/qwe.py`
Через питон
- http://qaru.site/questions/1297/how-do-i-copy-a-file-in-python

### Сменить пароль  linux
- https://losst.ru/kak-smenit-parol-v-linux


### Копирование файлов с одной машины, на другую

Я обычно юзаю **CyberDuck** или **Git**

или можно с помощь **scp** (устаавливает ssh):
- [How to Securely Transfer Files Between Servers with scp](https://www.linux.com/learn/intro-to-linux/2017/2/how-securely-transfer-files-between-servers-scp)

```
C одного сервера на другой
     scp username1@hostname1:/path/to/file username2@hostname2:/path/to/other/file
Со своей машины на другую
     scp /path/to/local/file username@hostname:/path/to/remote/file
С другой машины на свою
     scp username@hostname:/path/to/remote/file /path/to/local/file
Если нужен порт 
     scp -P 1234 username@hostname:/path/to/remote/file /path/to/local/file
     scp root@11.222.333.4:/root/dump.sql /Users/Andrew/downloads
```

### Сжимание файлов и папок
tar что бы сжать файл(ы), папку.
- https://help.ubuntu.ru/wiki/tar
- https://ru.wikipedia.org/wiki/Tar
```
Архивирование папки
    tar -pvczf bkup.tar.gz asd
Архивирование файла
    tar -pvczf bkup.tar.gz qwe.py
Архивирование файла, с путем папок внутри
    tar -pvczf bkup.tar.gz /Users/Andrew/desktop/asd/qwe.py
```

### Команды локального сервера
```
cd /Users/Andrew/w_projects/my_project/
source /Users/Andrew/w_projects/my_project/venv/bin/activate
```

### Команды боевого сервера
```
cd /root/my_project
source /root/my_project/venv/bin/activate
 
service gunicorn restart
service nginx restart
service gunicorn_kuskoproject restart
reboot

./manage.py migrate
./manage.py collectstatic
./manage.py collectstatic --no-default-ignore --noinput
```

## Ssh key для сервера
Создание открытого SSH-ключа
- https://git-scm.com/book/ru/v1/Git-%D0%BD%D0%B0-%D1%81%D0%B5%D1%80%D0%B2%D0%B5%D1%80%D0%B5-%D0%A1%D0%BE%D0%B7%D0%B4%D0%B0%D0%BD%D0%B8%D0%B5-%D0%BE%D1%82%D0%BA%D1%80%D1%8B%D1%82%D0%BE%D0%B3%D0%BE-SSH-%D0%BA%D0%BB%D1%8E%D1%87%D0%B0
```
# Создать
    ssh-keygen
# Посмотреть ключ
    cat ~/.ssh/id_rsa.pub
# Удалить
    ssh-keygen -R 188.166.171.254`
```

## Другие пользователи системы
**Зайти за другого пользовтаеля**
`su - username`

## Установленные пакеты и версии
```
# посмотреть
    pip freeze
# Скопироать в файл requirements.txt
    pip freeze > requirements.txt
# Скопироать в папку main_files, файл requirements.txt
    pip freeze > main_files/requirements.txt
# Установить из файла requirements.txt
    pip install -r requirements.txt
# Переустановка пакетов
    pip install -Ur requirements.txt
    pip install -U -r
```

## Запущенные процессы
```
# Все запущенные процессы
    ps aux
# Процессы, запущенные с помощью manage.py
    ps aux | grep -i manage
    ps aux | grep -i gunicorn
# Остановить процесс
    kill -9 30144
# Остановить процесс на порте
    Find:
        [sudo] lsof -i :3000
    Kill:
        kill -9 <PID>
    или
    - https://stackoverflow.com/questions/9346211/how-to-kill-a-process-on-a-port-on-ubuntu
        kill -9 $(lsof -i TCP:8000 | grep LISTEN | awk '{print $2}')
# Остановить все процессы с одинаковым названием
    pkill -f python
    pkill -f runserver
    pkill -f gunicorn

# Процессы запущенные на порте
    lsof | grep 35729`
# Посмотреть кто какие порты слушает
    netstat -tulnp

# Посмотреть через питон, открыт ли порт
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1',80))
    if result == 0:
       print("Port is open")
    else:
       print("Port is not open")
    sock.close()
```

## Создание файлов и папок
```
# Создать папку
    sudo mkdir folder

# Наделение правами
    # Всем открыто в папке**
    # 777 - всеобщий доступ
    # 755 - доступ по умолчанию для общей папки типа opt или root

        chmod -R 777 /opt

        chown -R root:root /root
        chmod -R ug+r /root

        chown -R www-data:www-data /
        sudo chmod -R o+rwx /directory

# Удаление папки
    rm  -rf /path/
# Очистка папки
    rm -r /path/

# Войти в окружение
    cd /root/my_project
    source /root/my_project/venv/bin/activate
```

## Shell
**Питоновский shell без окружения** 
`python`

**shell окружения**
```
./manage.py shell
python manage.py shell
```

**Пример использования*
```
import math
from b_page import qwe_function, asd_function
qwe function(q=1, w=2)
```

## Миграции
```
# Создать миграции
    ./manage.py makemigrations

# Мигрировать (согдать столбики в базе данных)
    ./manage.py migrate

    # Отдельное приложение проекта
        python manage.py notebooks

    # Вернуться к прошлой миграции**
        ./manage.py migrate *app_name* 0011
        ./manage.py migrate hotel_site 0036 --fake

    # Обозначить миграции как пройденную
        python manage.py migrate --fake

# Показать миграции
    python manage.py showmigrations
    python manage.py showmigrations notebooks

# Убрать все миграции**
    python manage.py migrate --fake notebooks zero
```

## nginx
```
sudo nano /etc/nginx/nginx.conf
sudo nano /etc/nginx/sites-available/my_project
sudo nano /etc/init/gunicorn.conf
sudo nano /root/my_project/firstsite/settings.py
```

## Установить java 
- https://stackoverflow.com/questions/24342886/how-to-install-java-8-on-mac
```
    brew cask install java
    brew tap caskroom/versions
    brew cask install java8

# To get a list of all older versions of java: 
    brew tap caskroom/versions
# and then use 
    brew search java
```

# Code style // стиль кода // стиль написания
** # todo: найти где-то в заметках уже десть дубликат
названия файлов:
```
vies.py
utils.py
functions.py
serializers.py
filters.py
handlers.py
signal_handlers.py
fixtures.py
logs.py

routes.py / urls.py

admin.pu
admin_filters.py

settings.py
constants.py

models.py
managers.py

celery.py
reddis.py
dbroutes.py

base.html
main.html
profile.html
```
```
fetch_my_special_data()  <- подобное название для каких-то далеких запросов. типа request_
retrive_my_special_data()
get_my_special_data()
request_some_resourse()
is_admin = True  //  is_mega_absolute_user
collect_something = ...
handle_error / processing
make_admin = ... 
crate_human = ...
_data, error // data, _error = ...  <- если функция может посылать значение или ошибку
```

**Переменные написаны большими буквами через нижнее подчеркивание**
в настройках те, что меняются или получаются из окружения
`SERVICE_HOST = os.environ.get("SERVICE_HOST")`  <- required value
`MY_SPECIAL_VARIABLE = os.environ.get("MY_SPECIAL_VARIABLE", "my_special_var_default_value")`  <- no required value
Те, что не меняются и в принципе не могут измениться. (допустим текстовые...)
находятся в файле `constants.py`
**В случае мапинга**
Если словарь, то ключ лучше обозначить отдельно 
```
MY_MAP_KEY = "key that may change"
SUPER_MAP = {
    MY_MAP_KEY: "specail vlue",
}
```
