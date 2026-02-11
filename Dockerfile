# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies for matrix-nio (olm)
RUN apt-get update && apt-get install -y \
  build-essential \
  libolm-dev \
  git \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final stage
FROM python:3.11-slim

# Create a non-root user
RUN useradd -m -u 1000 botuser

WORKDIR /app

# Install runtime dependencies for matrix-nio (libolm)
RUN apt-get update && apt-get install -y \
  libolm3 \
  && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY bot.py config.py healthcheck.py requirements.txt ./

# Create data directory and set permissions
RUN mkdir -p /app/data && chown -R botuser:botuser /app/data

# Switch to non-root user
USER botuser

# Environment variables
ENV PYTHONUNBUFFERED=1

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python healthcheck.py || exit 1

# Run the bot
CMD ["python", "bot.py"]
