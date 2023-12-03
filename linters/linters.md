

# Линтеры 

Moscow Python Meetup №86. Денис Аникин. Базовый кодовый стиль хорошего Python-бэкенда
https://www.youtube.com/watch?v=G3JKtB8tgvg
Интерактивный и холиварный доклад про линтеры / Никита Соболев (wemake.services)
https://www.youtube.com/watch?v=7IVCOzL41Lk

pep 8

ruff - посмотри на технологию. Новый линтер. вроде прям огонь. 
правит сразу весь код за тобой и заменяет многие линтеры ниже
Ruff недавно представил ruff formatter

perflint - устраняет некоторые анти-паттерны, убивающие производительность

Black - форматирует код и импорты
Isort - форматирует 
Flake hell - очень жесткий линтер
pylint - хороший линтер как блэк или flake8. медленный, не умеет автоправки
mypy - линтер для аннотаций типов
autoflake - удаление мертвого кода 
pyupgrade - переписывает код на новыую версию 
eradicate - убирает лишние комментарии (закомментированный код)
docformatter, pydocstyle - правит докстринги

numpy, airflow, pandas-vet, flynt, mccabe, pep8-naming, pycodstyle

pybetter - правит заурядные косяки 

    # BEFORE
    def p(a=[]):
        print(a)
      
    # AFTER
    def p(a=None):
        if a is None:
            a = []
        
        print(a)

pep 257 про докформаты


Некоторые полезные решения для ускорения написания кода

    — Sourcery (правил меньше, чем у ruff, но несколько раз он находил что-то дополнительно). Пока пилотируем. Правил около 200
    — Tabnine
    — Или Code whisperer
    — Copilot пока лучше всех, но не работает без VPN и аккаунта за 100S
    — Можно использовать ChatGPT 3.5, Bard, GigaChat, TheB.Al


аннотации типов

    — Берете ruff
    — Берете туру
    — Включите режим strict в туру
    — Включаете все правила в ruff
    — Они вас заставят


- https://github.com/regebro/ругота позволяет оценить «дружелюбность» вашего пакета
- https://github.com/iendrikseip/vulture ищет мертвый код по всему проекту
- https://github.com/dropbox/pyannotate выводит аннотации для вашего кода (но работа довольно ручная)
- https://github.com/Jellezifetra/autelyping добнеляет типовые аннотации (не идеально)
- https://github.com/bndr/pycycle обнаруживает циклические импорты (тесты?)
- https://github.com/Instagram/Fixil любопытный фреймворк для автоисправлений кода (!)
- https://aithub.com/lyz-code/autoimport сам добавляет нужные импорты
— https://github.com/pyupio/safety проверяет безопасность проектов
- https./althub.com/ingmaas/deptry ищет неиспользуемые, пропущенные, транзитивные зависимости


taskfile justfile makefile