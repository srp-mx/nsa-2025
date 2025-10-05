#!/bin/bash
set -e

# This script sets a development environment in demo mode (using SQLite).

# Clean all the media files
rm -rf ./media/*
rm -rf ./db.sqlite3

# Set demo mode environment variable
export DEMO=True

echo "Running in DEMO mode with SQLite database."

# Configure the Django settings for testing
echo "Setting up the database..."
python manage.py makemigrations
python manage.py migrate --noinput

echo "Loading initial data..."
python manage.py loaddata initial_data.json

# Create a superuser for testing
echo "Creating superuser..."
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=admin@example.com
export DJANGO_SUPERUSER_PASSWORD=admin
python manage.py createsuperuser --noinput

# Create test users
echo "Generating test users..."
python manage.py generate_users

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the Django development server
echo "Starting the Django development server..."
python manage.py runserver
