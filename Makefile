.PHONY: check test lint migrate-plan dev

dev:
	python manage.py runserver 0.0.0.0:8001

check:
	python manage.py check
	python manage.py makemigrations --check --dry-run

migrate-plan:
	python manage.py migrate --plan

test:
	python manage.py test apps.accounts apps.tenants

lint:
	black --check apps core
	isort --check-only apps core
	flake8 apps core
