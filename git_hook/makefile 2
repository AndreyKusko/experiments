install:
	pip freeze | grep -v "^-e" | xargs pip uninstall -y
	pip3 install -r requirements.txt
	pre-commit install --hook-type pre-push

