# Bitcoin Options Alert System - Docker Configuration
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directories for models and data
RUN mkdir -p models data

# Expose port for web services (Railway/Cloud Run)
EXPOSE 8080

# Set environment variable for port
ENV PORT=8080
ENV PYTHONPATH=/app

# Create a startup script that trains model if needed and runs the system
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Run the application
CMD ["/app/docker-entrypoint.sh"]