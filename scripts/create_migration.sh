#!/bin/bash

# Check if message parameter is provided
if [ -z "$1" ]; then
    echo "Usage: ./create_migration.sh 'migration message'"
    exit 1
fi

# Replace spaces with underscores in the message
message=$(echo "$1" | tr ' ' '_')

# Get the current timestamp
timestamp=$(date +"%Y%m%d%H%M%S")

# Create migration with timestamp and modified message
alembic revision --autogenerate -m "${timestamp}_${message}"

# Show created migration files
echo "Created migration files:"
ls -l alembic/versions/*.py | tail -n 1