# Multi-stage Dockerfile for Trapper Keeper MCP

# Build stage
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy dependency files first for better caching
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Install build tools and create wheel
RUN pip install --no-cache-dir --upgrade pip hatchling hatch-vcs build && \
    SETUPTOOLS_SCM_PRETEND_VERSION_FOR_TRAPPER_KEEPER_MCP=0.1.0 python -m build --wheel

# Runtime stage
FROM python:3.11-slim

# Build arguments
ARG BUILD_DATE
ARG VERSION
ARG REVISION

# Labels
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.title="Trapper Keeper MCP" \
      org.opencontainers.image.description="A Model Context Protocol server for intelligent document extraction and organization" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.vendor="asachs01" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/asachs01/trapper-keeper-mcp" \
      org.opencontainers.image.documentation="https://github.com/asachs01/trapper-keeper-mcp#readme"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r trapper && useradd -r -g trapper -m -d /app -s /sbin/nologin trapper

# Set working directory
WORKDIR /app

# Copy wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/

# Install the application
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl

# Copy configuration files
COPY --chown=trapper:trapper .env.example /app/.env.example

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/.trapper-keeper && \
    chown -R trapper:trapper /app

# Switch to non-root user
USER trapper

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TRAPPER_KEEPER_HOME=/app/.trapper-keeper \
    TRAPPER_KEEPER_LOG_LEVEL=INFO

# Expose MCP server port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Default command - run the MCP server
ENTRYPOINT ["trapper-keeper-mcp"]
CMD ["--host", "0.0.0.0", "--port", "3000"]
