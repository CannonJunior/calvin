#!/bin/bash

echo "Starting Earnings Dashboard with MCP Integration..."

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Warning: Ollama is not running on localhost:11434"
    echo "Please start Ollama first: ollama serve"
fi

# Start the HTTP server
echo "Starting HTTP server on http://localhost:8080"
npm run dev