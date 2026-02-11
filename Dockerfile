FROM python:3.11-slim

# Create a non-root user
RUN useradd -m -u 1000 botuser

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

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
