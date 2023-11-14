superuser:
	python3 ./manage.py createsuperuser
startapp:
	python3 ./manage.py startapp ${name}
migrate:
	python3 ./manage.py makemigrations ${app}
	python3 ./manage.py migrate
serv:
	# python3 ./manage.py runserver 8001
	uvicorn main.asgi:app --reload --port 8002
shell:
	python3 ./manage.py shell_plus
lint:
	isort --check-only --diff --recursive .
	black --check --diff .
test:
	pytest -n 6
