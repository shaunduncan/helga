# Multi-stage build for smaller, more secure images
# Stage 1: Builder
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory for builder stage
WORKDIR /build

# Copy only requirements first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip==24.0 setuptools==69.5.1 wheel==0.43.0 && \
    pip install -r requirements.txt

# Copy application code
COPY . /app
WORKDIR /app

# Install the application
RUN pip install .

# Stage 2: Runtime
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    libffi8 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r helga && useradd -r -g helga -u 1000 helga

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy settings file
COPY --chown=helga:helga settings_docker.py /etc/helga_settings.py

# Create directory for logs and data
RUN mkdir -p /var/log/helga /var/lib/helga && \
    chown -R helga:helga /var/log/helga /var/lib/helga

# Switch to non-root user
USER helga

# Set working directory
WORKDIR /home/helga

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import helga; print('OK')" || exit 1

# Expose any ports if needed (uncomment if webhooks are used)
# EXPOSE 8080

# Set entrypoint and default command
ENTRYPOINT ["/opt/venv/bin/helga"]
CMD ["--settings=/etc/helga_settings.py"]

# Labels for metadata
LABEL org.opencontainers.image.title="Helga Chat Bot" \
      org.opencontainers.image.description="A full-featured chat bot for Python 3.8+ with plugin support" \
      org.opencontainers.image.url="https://github.com/shaunduncan/helga" \
      org.opencontainers.image.documentation="https://helga.readthedocs.org" \
      org.opencontainers.image.source="https://github.com/shaunduncan/helga" \
      org.opencontainers.image.vendor="Shaun Duncan" \
      org.opencontainers.image.licenses="MIT OR GPL-3.0-or-later"

# Made with Bob
