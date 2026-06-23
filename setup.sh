#!/bin/bash

# AutoPilot Quick Setup Script
# This script helps you configure AutoPilot in 5 minutes

set -e

echo "🚀 AutoPilot Quick Setup"
echo "========================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📋 Creating .env from template..."
    cp .env.example .env
    echo "✓ .env created. Edit it with your credentials:"
    echo "  vim .env"
    echo ""
fi

# Check if Ollama is running
echo "🔍 Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is running"
else
    echo "⚠️  Ollama is NOT running"
    echo "   Start it in another terminal: ollama serve"
    echo ""
fi

# Activate or create venv
if [ ! -d venv ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🐍 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
python -m pip install --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Test imports
echo "🧪 Testing imports..."
python -c "
import config
import email_fetcher
import scheduler
import slack_sender
import summarizer
print('✓ All imports successful')
"

echo ""
echo "========================"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your credentials (vim .env)"
echo "2. Ensure Ollama is running (ollama serve)"
echo "3. Start the server: python main.py"
echo "4. In another terminal, test: curl -X POST http://localhost:8000/trigger"
echo ""
echo "For help, see README.md"
