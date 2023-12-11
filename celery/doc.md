# Celery 
дока 
- http://docs.celeryproject.org/en/latest/reference/celery.app.task.html
- http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html
- https://habr.com/post/269347/
- http://devacademy.ru/posts/ochered-soobschenij-i-asinhronnyie-zadachi-s-pomoschyu-celery-i-rabbitmq/
- https://khashtamov.com/ru/celery-best-practices/
- https://pawelzny.com/python/celery/2017/08/14/celery-4-tasks-best-practices/

**в общем после всех мучений кроме обычного сервера в виртуальном окружении нужно запустить:**
**сервер celerу**
`celery -A my_project_mega_tasks worker --loglevel=info`
**брокер** 
`rabbitmq-server`
или 
`redis-server`
**flower**

## Начало 

### Установка
**Сам Celery**
`pip install celery`

### Брокеры
Или то или другое, выбери что-ниубудь 
Redis, RabbitMQ (см ниже)

### Создание файлов в директории проекта
**tasks.py**
```
    from celery import Celery

# Пример 1. Настройки celery 
        # заработает и без конфигурационного файла, просто взять и запустить всю хурму
    celery_app = Celery('tasks', broker='redis://localhost', backend='redis://localhost',)  
# Пример 2.  конфигурации в отдельных строчках
     celery_app = Celery('tasks')
     app.conf.broker_url = 'redis://localhost:6379/0' # также можно делать настройку в таком виде
# Пример 3.  Вынести конфигурации в отдельный файл
     celery_app = Celery('tasks')
     celery_app.config_from_object('celeryconfig')  # В данном примере файл celeryconfig.py находится в конрневой папке проекта

    import logging
    logger = logging.getLogger(__name__)

    @celery_app.task(ignore_result=True)  # Типа результат игнорируется (блин даже хз за чем такое делать)
    def print_hello():
        print('hello there')

    @celery_app.task  # Данная запись - декоратор - необходима привязывает функцию к celery
    def task1(x, y):
        z = 1
        for i in range(x, y):
            z = z * i
        logger.error('task1 (%s * %s) is ready = %s' % (x, y, z) )
        return z
``` 

### Или создание папки в директории проекта
понадобится файл __init__.py в директории папки
**my_project_mega_tasks папка**
```
my_project_mega_tasks
    |- __init__.py
```
**__init__.py**
```
from .tasks import *
```
**tasks.py такой же как и выше**

### Конфигурационный файл celeryconfig.py

```
// Следующие 2 строачки основные, должны присутсвуввать вроде как
    broker_url = 'amqp://localhost'     
    result_backend = 'amqp://localhost'
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'Europe/Oslo'
    enable_utc = True
```

### Поднятие серверов
Поднять сервер брокера (Reddis, RabbitMQ)
```
# Запустить селери
    celery -A tasks worker --loglevel=info`
# Убить Celery**
    ps auxww | grep 'celery worker' | awk '{print $2}' | xargs kill -9

# Если папка
    celery -A my_project_mega_tasks worker --loglevel=info
```

### Выполнение задач и проверка
```
# Импортирование задач**
Создание задачи
    from my_project_mega_tasks import task1

    # Простое выплнение задачи не асинхронное
        t = task1(1, 1000000)  
    # Как раз асинхронное выполнение
        t = task1.delay(1, 1000000)  
    # более мощное асинхронное выполнение
        t = task1.apply_async((1, 324023))
        # или
        t = task1.apply_async(args=(1, 324023), priority=1)

    # Проверить выполнена ли задача
        t.ready()  
        >>>  True
        >>>  False

    # Получить результат задачи
        t.get()
        >>>  'Какое-то число'
```

### Очереди задач и приоритеты.
Вообще celery херово поддерживает приоритеты задач.
- https://stackoverflow.com/questions/15809811/celery-tasks-that-need-to-run-in-priority
- http://docs.celeryproject.org/en/master/faq.html#does-celery-support-task-priorities

роутинг всей хурмы
- http://docs.celeryproject.org/en/latest/userguide/routing.html

Лучше использовать отдельные воркеры для конкретных задач
`celery -A my_project_mega_tasks worker -l info -Q high`
**celeryconfig.py**
```
    from kombu import Exchange, Queue

    task_queues = (
        Queue('high', Exchange('high'), routing_key='high'),
        Queue('normal', Exchange('normal'), routing_key='normal'),
        Queue('low', Exchange('low'), routing_key='low'),
    )
    task_routes = {
        'my_project_mega_tasks.tasks.task1': {'queue': 'high'},
        'my_project_mega_tasks.tasks.task2': {'queue': 'normal'},
        'my_project_mega_tasks.tasks.task3': {'queue': 'low'},
    }
```
**Запуск отдельного воркера**
_celery worker -Q priority_high_

### Redis
Redis не очеь хорошо работает с приритетами задач.  
**установка**
`pip install redis`

**Настройка конфигурации celery** 
Можно записать подобным способом `redis://localhost:6379/0` Этот хост redis по-умолчанию
```
    broker_url = 'redis://localhost'
    result_backend = 'redis://localhost'
```

**Поднять сервер редиса**
поднять нужно в виртуальном окружении
`redis-server`


### RabbitMQ 
_"Хрен разберешся в нем"_
http://www.rabbitmq.com/install-homebrew.html
http://docs.celeryproject.org/en/latest/getting-started/brokers/rabbitmq.html
```
# Установка
    brew install rabbitmq
    pip install rabbitmq

# Настройка конфигурации celery
    broker_url = 'amqp://localhost'
    result_backend = 'amqp://localhost'

# Перед запуском серверанужно прописать путь
    PATH=$PATH:/usr/local/sbin

# Поднять сервер rabbitMQ
  поднять нужно в виртуальном окружении
    rabbitmq-server

# Убить сервер rabbitMQ
    rabbitmqctl stop

# Посмотреть дополнительные процессы rabbitMQ
    ps aux | grep epmd
    ps aux | grep erl
# Убить дополнительные процессы
    sudo pkill -9 -f epmd
    sudo pkill -9 -f erl
```

### Отслеживание задач
**Очень удобное отслеживание при помощи Flower**
https://celery.readthedocs.io/en/latest/userguide/monitoring.html#flower-real-time-celery-web-monitor
```
# Установка
    pip install flower

# Старт сервера fower
    Если Reddis
        celery -A tasks flower
    если папка 
        celery -A my_project_mega_tasks flower
    Если RabbitMQ
        celery flower --broker=amqp://guest:guest@localhost:5672//

# По умолчанию таски можно будет посомтреть по ссылке**
- http://127.0.0.1:5555/tasks

# Использовать дургой порт (точно работает если reddis)** 
celery -A my_project_mega_tasks flower --port=6666

# Примеры
    t1 = task1.delay(1, 224023)
    t2 = task2.delay(1, 224023)
    t3 = task3.delay(1, 224023)

    t1 = task1.apply_async(1, 224023, priority=0)
    t2 = task2.apply_async(1, 224023, priority=4)
    t3 = task3.apply_async(1, 224023, priority=9)

    s(arg1, arg2, kwarg1='x', kwargs2='y').apply_async()

    t1 = task1.apply_async(args=(1, 114023), priority=0)
    t2 = task2.apply_async(args=(1, 114023), priority=4)
    t3 = task3.apply_async(args=(1, 114023), priority=8)

    t1 = task1.apply_async(args=(1, 114023), queue='default', priority=0)
    t2 = task2.apply_async(args=(1, 114023), queue='default', priority=4)
    t3 = task3.apply_async(args=(1, 114023), queue='default', priority=8)

    t1 = task1.s(1, 224023).apply_async(priority=0)
    t2 = task2.s(1, 224023).apply_async(priority=4)
    t3 = task3.s(1, 224023).apply_async(priority=4)

    print(t1.ready())
    print(t2.ready())
    print(t3.ready())
```
