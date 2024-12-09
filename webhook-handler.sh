#!/bin/bash

# Navigate to your Django app's repository
# Activate your virtual environment
cd /home/airdec/public_html/api.airdec.net
source /home/airdec/virtualenv/public_html/api.airdec.net/3.11/bin/activate

# Pull the latest changes from the specific branch
git stash --include-untracked
git pull
git stash apply


# Run Django management commands
# python manage.py makemigrations
python manage.py migrate

touch /home/airdec/public_html/api.airdec.net/tmp/restart.txt