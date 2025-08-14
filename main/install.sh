#!/bin/bash

# SeatSeeker Installation Script
# UC Merced Course Availability Notifier

set -e

echo "🎓 SeatSeeker - UC Merced Course Availability Notifier"
echo "=================================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    echo "Please install pip3 and try again."
    exit 1
fi

echo "✅ pip3 found: $(pip3 --version)"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Setup database
echo "🗄️  Setting up database..."
python run.py setup

# Create .env file from template
if [ ! -f .env ]; then
    echo "⚙️  Creating configuration file..."
    cp config.env .env
    echo "✅ Configuration file created: .env"
    echo "📝 Please edit .env with your email settings before running the program."
else
    echo "✅ Configuration file already exists: .env"
fi

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your email settings"
echo "2. Start the dashboard: python run.py dashboard"
echo "3. Start the scheduler: python run.py scheduler"
echo ""
echo "📖 For more information, see README.md"
echo ""
echo "🚀 Happy course hunting!"
