#!/bin/bash
set -e

echo "=== Audit Logging System Setup ==="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install audit-client as editable package
echo "Installing audit-client library..."
pip install -e audit-client/

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo ""
    echo "Docker is available. You can use:"
    echo "  docker-compose up -d postgres    # Start PostgreSQL"
    echo "  make migrate                     # Run migrations"
    echo "  make start                       # Start audit service"
else
    echo ""
    echo "Docker not found. Please install Docker or configure PostgreSQL manually."
    echo "Set DATABASE_URL environment variable to your PostgreSQL connection string."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Start PostgreSQL: docker-compose up -d postgres"
echo "2. Run migrations: make migrate"
echo "3. Start service: make start"
echo "4. Run tests: make test"
echo ""
echo "See README.md for more details."
