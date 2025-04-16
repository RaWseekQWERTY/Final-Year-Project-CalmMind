# Base image with Python 3.11
FROM python:3.11

# Suppress pip warnings about running as root
ENV PIP_NO_WARN_ROOT=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    build-essential \
    gcc \
    g++ \
    make \
    libffi-dev \
    python3-dev \
    libc-dev \
    netcat-openbsd

# Install Node.js 18.x and npm
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm

# Clean up apt cache
RUN rm -rf /var/lib/apt/lists/*

# Copy Node.js package files first for better caching
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Install TailwindCSS dependencies
RUN npm install -D tailwindcss postcss autoprefixer

# Initialize TailwindCSS configuration
RUN npx tailwindcss init

COPY ./static ./static
# Build TailwindCSS
RUN npx tailwindcss -i ./static/css/tailwind-input.css -o ./static/css/output.css --minify

# Copy Python requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Download TinyLlama
RUN mkdir -p /app/tinyllama-base && \
    huggingface-cli download TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T --local-dir /app/tinyllama-base

# Copy the rest of the application
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "calmmind.wsgi:application", "--bind", "0.0.0.0:8000"]