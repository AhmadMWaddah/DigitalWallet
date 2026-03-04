#!/bin/bash
# Setup Script
# Usage: ./scripts/setup.sh

set -e

echo "=== Digital Wallet Project Setup ==="

# Activate virtual environment
echo "Activating virtual environment..."
source .env_digital_wallet/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate --settings=core.settings.dev

# Create superuser prompt
echo ""
echo "Setup complete!"
echo "To create a superuser, run: python manage.py createsuperuser --settings=core.settings.dev"
echo "To run the server: python manage.py runserver 8500 --settings=core.settings.dev"
