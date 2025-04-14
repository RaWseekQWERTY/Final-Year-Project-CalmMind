# Base image with Python 3.11
FROM python:3.11

# Suppress pip warnings about running as root
ENV PIP_NO_WARN_ROOT=1

# Set workdir
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    gcc \
    g++ \
    make \
    libffi-dev \
    python3-dev \
    libc-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu


RUN mkdir -p /app/tinyllama-base && \
    huggingface-cli download TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T --local-dir /app/tinyllama-base

# Copy project files
COPY . .

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Command to run the application
CMD ["gunicorn", "calmmind.wsgi:application", "--bind", "0.0.0.0:8000"]