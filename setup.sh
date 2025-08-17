#!/bin/bash

# Django deployment setup script for AWS Lightsail

echo "Setting up Django application..."

# Install Python dependencies
pip3 install -r requirements.txt

# Set environment variables
export DJANGO_SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

# Create necessary directories
mkdir -p staticfiles
mkdir -p media

# Collect static files
python3 manage.py collectstatic --noinput

# Run database migrations
python3 manage.py migrate

# Compile translation messages
python3 manage.py compilemessages

echo "Django setup completed!"
echo "Don't forget to:"
echo "1. Set DJANGO_SECRET_KEY environment variable in your deployment"
echo "2. Configure Apache virtual host"
echo "3. Restart Apache service" 