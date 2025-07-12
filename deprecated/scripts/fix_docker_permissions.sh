#!/bin/bash

# Fix Docker Permissions Script for Calvin Stock Prediction Tool

echo "🔧 Fixing Docker Permissions"
echo "============================"
echo ""

# Check if Docker is installed as snap
if snap list docker &>/dev/null; then
    echo "✅ Docker snap detected"
    DOCKER_TYPE="snap"
elif command -v docker &>/dev/null; then
    echo "✅ Docker binary detected"
    DOCKER_TYPE="regular"
else
    echo "❌ Docker not found"
    exit 1
fi

# Check current user groups
echo "Current user groups: $(groups $USER)"

# Check if user is in docker group
if groups $USER | grep -q '\bdocker\b'; then
    echo "✅ User is already in docker group"
else
    echo "⚠️ User is not in docker group. Adding..."
    
    # Add user to docker group
    if sudo usermod -aG docker $USER; then
        echo "✅ User added to docker group"
        echo "📝 Note: Group changes will take effect after logout/login or running 'newgrp docker'"
    else
        echo "❌ Failed to add user to docker group"
        exit 1
    fi
fi

# For snap Docker, we might need to connect the interface
if [ "$DOCKER_TYPE" = "snap" ]; then
    echo "🔌 Checking snap Docker interfaces..."
    if sudo snap connect docker:docker-executables || true; then
        echo "✅ Docker snap interfaces connected"
    fi
fi

echo ""
echo "🧪 Testing Docker access..."

# Test Docker access with current session
if docker info &>/dev/null; then
    echo "✅ Docker is accessible!"
    echo "🚀 You can now run: ./scripts/init_system.sh"
    exit 0
else
    echo "⚠️ Docker still not accessible in current session"
    echo ""
    echo "📋 To apply group changes, choose one of:"
    echo "1. Run: newgrp docker"
    echo "2. Log out and log back in"
    echo "3. Restart your terminal"
    echo ""
    echo "Then test with: docker info"
    echo "Once Docker is accessible, run: ./scripts/init_system.sh"
fi

echo ""
echo "🔍 Debug Information:"
echo "User: $(whoami)"
echo "Groups: $(groups)"
echo "Docker socket: $(ls -la /var/run/docker.sock 2>/dev/null || echo 'Not found')"
echo "Docker processes: $(ps aux | grep dockerd | grep -v grep || echo 'None')"