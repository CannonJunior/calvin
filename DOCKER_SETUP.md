# Docker Setup Guide for Calvin Stock Prediction Tool

## Current Status
✅ Docker is installed  
✅ Docker Compose is installed  
✅ API keys configured (Tavily key detected)  
❌ Docker daemon needs to be started

## Start Docker Daemon

### Option 1: Start Docker Service (Recommended)
```bash
# Start Docker daemon
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Add your user to docker group (to avoid sudo)
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker
```

### Option 2: Start Docker Desktop (if installed)
```bash
# If using Docker Desktop, start it from applications menu
# Or via command line:
systemctl --user start docker-desktop
```

### Option 3: Manual Docker Start
```bash
# Start dockerd manually (temporary)
sudo dockerd &
```

## Verify Docker is Running
```bash
# Test Docker access
docker info

# Should show Docker system info without permission errors
```

## Continue Calvin Setup

Once Docker is running, continue the setup:

```bash
# Run the initialization script again
./scripts/init_system.sh

# Or manual steps:
# 1. Export API keys
source config/export_api_keys.sh

# 2. Start services  
docker-compose up -d

# 3. Initialize AI models
docker-compose exec ollama ollama pull llama3.1:8b
docker-compose exec ollama ollama pull qwen2.5:7b

# 4. Load S&P 500 data
docker-compose exec backend uv run scripts/load_sp500_data.py
```

## Troubleshooting

### Permission Denied Error
If you get permission denied:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker

# Or restart your session
```

### Docker Service Not Found
If docker service is not found:
```bash
# Install Docker if missing
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Or on Ubuntu/Debian:
sudo apt update
sudo apt install docker.io docker-compose
```

### WSL/Linux Subsystem
If using WSL:
```bash
# Start Docker Desktop on Windows first
# Then in WSL:
docker context use default
```

## Next Steps After Docker Starts

1. **Re-run initialization**: `./scripts/init_system.sh`
2. **Access web interface**: http://localhost:3000
3. **Check API documentation**: http://localhost:8000/docs
4. **Monitor logs**: `docker-compose logs -f`

## API Keys Status
- ✅ **Tavily**: Configured (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...)
- ⚠️ **Polygon.io**: Placeholder - get free key at https://polygon.io/
- ⚠️ **Alpha Vantage**: Placeholder - get free key at https://www.alphavantage.co/
- ⚠️ **Financial Modeling Prep**: Placeholder - get free key at https://financialmodelingprep.com/

The system will work with limited functionality using yfinance and your Tavily key. For full functionality, add the other free API keys to `config/api_keys.env`.