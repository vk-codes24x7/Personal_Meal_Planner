#!/bin/bash

# Meal Planning Automation System Startup Script

echo "🍽️ Starting Meal Planning Automation System..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if requirements are installed
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found. Please run: pip install -r requirements.txt"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "⚠️  Ollama is not running. Starting Ollama..."
    echo "Please make sure Ollama is installed and run: ollama serve"
    echo "Then pull a model: ollama pull llama2"
    echo ""
    echo "Starting system anyway (will use fallback recipes)..."
fi

# Start the meal planning system
echo "🚀 Launching meal planner..."
python3 main.py start 