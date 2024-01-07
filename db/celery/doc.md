# Celery


запускается в терминале проекта

pip install celery



Celery 

    в терминале проекта под venv
        celery -A ma_saas worker -l INFO
		celery -A madirect_backgrounds worker -l INFO

    В общем терминале
        Rabbit mq для celery
                docker run -p 5672:5672 rabbitmq
        Reddis
            6379
            redis-server
    
    в терминале проекта под venv
        Flower
            Rabbit
                    celery flower --broker=amqp://guest:guest@localhost:5672//
            Redis
                    celery flower --broker=redis://guest:guest@localhost:6379/0



Либы 
django-celery-beat
установить еще redis 

    redis

