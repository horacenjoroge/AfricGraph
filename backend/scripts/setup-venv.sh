#!/bin/bash
# Setup script for creating Python virtual environment

set -e

echo "🚀 Setting up AfricGraph Python environment..."

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Check if Python 3.11+ is available
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "❌ Error: Python 3.11 or higher is required"
    echo "   Current version: $python_version"
    exit 1
fi

# Warn about Python 3.13 compatibility issues
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 13) else 1)"; then
    echo "⚠️  Warning: Python 3.13 may have compatibility issues with some packages"
    echo "   Consider using Python 3.11 or 3.12 for better compatibility"
    echo "   If you have python3.11 or python3.12, you can use:"
    echo "   python3.11 -m venv venv  (or python3.12 -m venv venv)"
    read -p "   Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Navigate to backend directory
cd "$(dirname "$0")/.." || exit 1

# Create virtual environment
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists at ./venv"
    read -p "   Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing virtual environment..."
        rm -rf venv
    else
        echo "✅ Using existing virtual environment"
        exit 0
    fi
fi

echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "📥 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "   source venv/bin/activate"
echo ""
