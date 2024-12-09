#!/bin/bash

# Define log file
LOG_FILE="../api-update-log.txt"

# Log function to add datetime tag
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Start logging
log "Script execution started."

# Navigate to your Django app's repository
log "Navigating to project directory."
cd /home/airdec/public_html/api.airdec.net || { log "Failed to navigate to project directory."; exit 1; }

# Activate your virtual environment
log "Activating virtual environment."
source /home/airdec/virtualenv/public_html/api.airdec.net/3.11/bin/activate || { log "Failed to activate virtual environment."; exit 1; }

# Pull the latest changes from the specific branch
log "Stashing changes."
git stash --include-untracked >> $LOG_FILE 2>&1
log "Pulling updates from Git."
git pull >> $LOG_FILE 2>&1
log "Applying stashed changes."
git stash apply >> $LOG_FILE 2>&1

# Run Django management commands
log "Running database migrations."
python manage.py migrate >> $LOG_FILE 2>&1

# Restart the application
log "Restarting the application."
touch /home/airdec/public_html/api.airdec.net/tmp/restart.txt

# End logging
log "Script execution completed."