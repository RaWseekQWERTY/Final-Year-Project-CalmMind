# Base image
FROM python:3.13-alpine

# Set workdir
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]
