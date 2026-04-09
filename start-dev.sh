#!/bin/bash

# ========== AgentForge Deployment Helper ==========

echo "🚀 AgentForge Deployment Helper"
echo "================================"

# Check Python version
echo ""
echo "Checking Python version..."
python --version

# Check if pip install has been done
echo ""
echo "Checking dependencies..."
pip list | grep fastapi > /dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
else
    echo "✅ Dependencies already installed"
fi

# Check for .env file
echo ""
echo "Checking environment configuration..."
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys"
    echo "   Then run this script again"
    exit 1
else
    echo "✅ .env file exists"
fi

# Start services
echo ""
echo "Starting services..."

# Redis
echo "🔴 Redis..."
redis-server &
REDIS_PID=$!
sleep 1

# ChromaDB
echo "📦 ChromaDB..."
mkdir -p storage/chroma
chroma run --path ./storage/chroma &
CHROMA_PID=$!
sleep 2

# FastAPI
echo "⚡ FastAPI..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
FASTAPI_PID=$!
sleep 3

echo ""
echo "✅ All services running!"
echo ""
echo "📍 Frontend: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for interrupt
wait

# Cleanup
echo ""
echo "Stopping services..."
kill $REDIS_PID $CHROMA_PID $FASTAPI_PID 2>/dev/null
echo "✅ Stopped"
