#!/bin/bash

# Navigate to your Django app's repository
cd /home/airdec/public_html/api.airdec.net

# Pull the latest changes from the specific branch
git pull

# Activate your virtual environment
source /home/airdec/virtualenv/public_html/api.airdec.net/3.11/bin/activate

# Run Django management commands
pip install -r requirements/dev.txt
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput