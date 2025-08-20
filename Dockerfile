# Multi-stage Dockerfile for ConceptNet MCP Server
# Optimized for production with development capabilities

ARG PYTHON_VERSION=3.11

# Build stage - for installing dependencies and building the package
FROM python:${PYTHON_VERSION}-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY README.md LICENSE ./

# Install the package
RUN pip install -e .

# Production stage - minimal runtime image
FROM python:${PYTHON_VERSION}-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser appuser

# Create app directory and logs directory
WORKDIR /app
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Copy Python environment from builder
COPY --from=builder /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app/src ./src
COPY --from=builder /app/README.md /app/LICENSE ./

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import conceptnet_mcp; print('OK')" || exit 1

# Expose default port for HTTP transport
EXPOSE 3001

# Default command (can be overridden by docker compose)
CMD ["python", "-m", "conceptnet_mcp.server"]