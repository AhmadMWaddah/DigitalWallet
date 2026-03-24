#!/bin/bash
# Digital Wallet Project Setup Script
# Usage: ./scripts/setup.sh

set -e

echo "======================================"
echo "  Digital Wallet Project Setup"
echo "======================================"
echo ""

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .env_digital_wallet/bin/activate

# Install production dependencies
echo "📦 Installing production dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "📦 Installing development dependencies..."
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install

# Run database migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --settings=core.settings.dev

# Create .env from .env.example if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration!"
fi

echo ""
echo "======================================"
echo "  ✅ Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Update .env with your configuration"
echo "  2. Create superuser: python manage.py createsuperuser --settings=core.settings.dev"
echo "  3. Run server: python manage.py runserver 8500 --settings=core.settings.dev"
echo ""
