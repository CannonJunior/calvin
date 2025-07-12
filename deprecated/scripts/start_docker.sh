#!/bin/bash

# Docker Startup Helper Script for Calvin Stock Prediction Tool

echo "🐳 Docker Startup Helper for Calvin Stock Prediction Tool"
echo "========================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Function to test Docker access
test_docker() {
    if docker info &> /dev/null; then
        echo "✅ Docker is running and accessible"
        return 0
    else
        return 1
    fi
}

# Check current Docker status
echo "🔍 Checking Docker status..."

if test_docker; then
    echo "✅ Docker is already running!"
    echo "🚀 You can now run: ./scripts/init_system.sh"
    exit 0
fi

echo "❌ Docker is not accessible. Let's try to start it..."

# Try different methods to start Docker
echo ""
echo "🔧 Attempting to start Docker daemon..."

# Method 1: systemctl (most common)
echo "Trying: sudo systemctl start docker"
if sudo systemctl start docker 2>/dev/null; then
    echo "✅ Docker service started with systemctl"
    sleep 3
    if test_docker; then
        echo "✅ Docker is now running!"
        
        # Add user to docker group for future access
        echo "🔐 Adding user to docker group for future access..."
        if sudo usermod -aG docker $USER 2>/dev/null; then
            echo "✅ User added to docker group"
            echo "💡 Note: You may need to log out and back in for group changes to take effect"
            echo "   Or run: newgrp docker"
        fi
        
        echo ""
        echo "🚀 Ready to continue! Run: ./scripts/init_system.sh"
        exit 0
    fi
fi

# Method 2: Try service command
echo "Trying: sudo service docker start"
if sudo service docker start 2>/dev/null; then
    echo "✅ Docker started with service command"
    sleep 3
    if test_docker; then
        echo "✅ Docker is now running!"
        echo "🚀 Ready to continue! Run: ./scripts/init_system.sh"
        exit 0
    fi
fi

# Method 3: Docker Desktop (if available)
if command -v "Docker Desktop" &> /dev/null || [ -f "/Applications/Docker.app/Contents/MacOS/Docker" ]; then
    echo "Trying to start Docker Desktop..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open -a Docker
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        systemctl --user start docker-desktop 2>/dev/null || true
    fi
    
    echo "⏳ Waiting for Docker Desktop to start..."
    for i in {1..30}; do
        if test_docker; then
            echo "✅ Docker Desktop is now running!"
            echo "🚀 Ready to continue! Run: ./scripts/init_system.sh"
            exit 0
        fi
        sleep 2
        echo -n "."
    done
    echo ""
fi

# If we get here, Docker couldn't be started automatically
echo ""
echo "❌ Could not start Docker automatically."
echo ""
echo "📋 Manual Steps to Start Docker:"
echo "================================"
echo ""

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "On Linux:"
    echo "1. sudo systemctl start docker"
    echo "2. sudo systemctl enable docker  # Start on boot"
    echo "3. sudo usermod -aG docker \$USER  # Add user to docker group"
    echo "4. newgrp docker  # Apply group changes"
    echo ""
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "On macOS:"
    echo "1. Start Docker Desktop from Applications"
    echo "2. Wait for Docker Desktop to be ready"
    echo ""
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    echo "On Windows:"
    echo "1. Start Docker Desktop"
    echo "2. Wait for Docker Desktop to be ready"
    echo ""
fi

echo "Common Issues:"
echo "• Permission denied: Add user to docker group"
echo "• Docker not installed: Install from https://docs.docker.com/get-docker/"
echo "• WSL: Make sure Docker Desktop is running on Windows"
echo ""

echo "🔍 Check Docker status with: docker info"
echo "🚀 Once Docker is running, execute: ./scripts/init_system.sh"

exit 1