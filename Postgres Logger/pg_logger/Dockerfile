FROM python:3.11-slim

# Install Node.js (Required for Reflex frontend compilation)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    gnupg \
    unzip \
    && curl -sL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Note: reflex init not needed - app already configured with rxconfig.py
# The frontend will compile on first run

# Expose ports
EXPOSE 3000 8000

# Set environment variable for Keyring in headless Docker
ENV PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

# Start Reflex in production mode
CMD ["reflex", "run", "--env", "prod", "--loglevel", "info"]
