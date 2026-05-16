#!/bin/bash

# Setup script for AI Financial Analyst

set -e

echo "========================================"
echo "AI Financial Analyst - Setup Script"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
required_version="3.10"

if ! python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "❌ Python 3.10+ required. Found: $python_version"
    exit 1
fi

echo "✓ Python version: $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your Gemini API key!"
    echo "   Get one at: https://makersuite.google.com/app/apikey"
else
    echo "✓ .env file already exists"
fi
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p data/raw data/processed data/vector_store
mkdir -p outputs/reports outputs/excel outputs/logs
echo "✓ Directories created"
echo ""

# Check for sample documents
echo "Checking for documents..."
if [ -z "$(ls -A data/raw)" ]; then
    echo "⚠️  No documents found in data/raw/"
    echo "   Please add your financial documents (PDF, Excel, CSV) to data/raw/"
else
    echo "✓ Documents found in data/raw/"
fi
echo ""

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GEMINI_API_KEY"
echo "2. Add your financial documents to data/raw/"
echo "3. Run: python scripts/ingest_documents.py"
echo "4. Run: streamlit run src/presentation/streamlit_app.py"
echo ""
echo "For CLI mode: python src/main.py"
echo ""
