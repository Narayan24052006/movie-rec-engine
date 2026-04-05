#!/bin/bash
# StreamRec — Full Rebuild & Run Script
# Run this from the movie-rec-engine directory

set -e
cd "$(dirname "$0")"

echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

echo "🔨 Clearing corrupted BuildKit cache..."
docker builder prune -f || true
docker system prune -f || true

echo "🔨 Rebuilding images with latest code fixes..."
docker-compose build --no-cache

echo "🚀 Starting containers..."
docker-compose up -d

echo ""
echo "✅ Done! Containers are starting up."
echo "   API trains models in ~90 seconds on first run."
echo ""
echo "   UI:  http://localhost:8501"
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
