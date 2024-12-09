#!/bin/bash

# Navigate to your Django app's repository
cd /home/airdec/public_html/api.airdec.net

# Pull the latest changes from the specific branch
git stash --include-untracked
git pull
git stash apply

# Activate your virtual environment
source /home/airdec/virtualenv/public_html/api.airdec.net/3.11/bin/activate

# Run Django management commands
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

touch /home/airdec/public_html/api.airdec.net/tmp/restart.txt