#!/bin/bash

# Load environment variables from .env file
set -a
source .env
set +a

# Extract database connection details from DATABASE_URL
DB_URL=$DATABASE_URL
DB_USER=$(echo $DB_URL | awk -F[:/@] '{print $4}')
DB_PASS=$(echo $DB_URL | awk -F[:/@] '{print $5}')
DB_HOST=$(echo $DB_URL | awk -F[:/@] '{print $6}')
DB_PORT=$(echo $DB_URL | awk -F[:/@] '{print $7}')
DB_NAME=$(echo $DB_URL | awk -F[:/@] '{print $8}')

# Create backup directory if it doesn't exist
BACKUP_DIR="database_backups"
mkdir -p $BACKUP_DIR

# Generate timestamp for backup file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${PROJECT_CODE}_${DB_NAME}_${TIMESTAMP}.sql"

echo "🔄 Starting database backup process..."

# Perform database backup
PGPASSWORD=$DB_PASS pg_dump \
    -h $DB_HOST \
    -p $DB_PORT \
    -U $DB_USER \
    -d $DB_NAME \
    -F p \
    -f $BACKUP_FILE

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "✅ Database backup created successfully: $BACKUP_FILE"
    
    echo "🔄 Running database migrations..."
    alembic upgrade head
    
    if [ $? -eq 0 ]; then
        echo "✅ Database migrations completed successfully"
    else
        echo "❌ Database migrations failed"
        echo "💡 You can restore the backup using:"
        echo "PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $BACKUP_FILE"
        exit 1
    fi
else
    echo "❌ Database backup failed"
    exit 1
fi