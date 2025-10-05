all: clear configure run

clear:
	rm -rf db/db.sqlite3 backend/migrations/0* media/*

configure:
	python3 manage.py makemigrations
	python3 manage.py migrate
	python3 manage.py createsuperuser
	python manage.py loaddata initial_data.json

run:
	python3 manage.py runserver
