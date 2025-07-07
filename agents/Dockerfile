# Agents Dockerfile for Calvin Stock Prediction Tool
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN pip install uv

# Create app directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Install dependencies
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install --no-deps -e .

# Copy agents and required modules
COPY agents/ ./agents/
COPY backend/app/ ./app/

# Create assets directory
RUN mkdir -p assets

# Expose port (if needed for agent services)
EXPOSE 8003

# Health check for agent availability
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD python -c "import asyncio; from agents.base_agent import BaseAgent; from agents.analysis_agent import AnalysisAgent; agent = AnalysisAgent(); print('Agents healthy')" || exit 1

# Run the agent orchestrator (or keep container running for orchestration calls)
CMD ["/app/.venv/bin/python", "-c", "import asyncio; print('Agent container ready'); asyncio.run(asyncio.sleep(86400))"]