#!/bin/bash
# Launcher script for Historical Term Analyzer Streamlit App

echo "🔍 Starting Historical Term Analyzer Web Interface..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
# Install required packages
pip install -r requirements.txt

echo "🚀 Launching Streamlit app..."
echo "Open your browser and go to: http://localhost:8501"

# Launch Streamlit app
streamlit run streamlit_app.py