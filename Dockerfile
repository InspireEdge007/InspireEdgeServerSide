# Use the official Python Alpine image from the Docker Hub
FROM python:3.10-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk update \
    && apk add --no-cache gcc musl-dev linux-headers postgresql-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

ENV PYTHONPATH="/app/inspire_edge_backend"

WORKDIR /app/inspire_edge_backend/

CMD gunicorn AI.wsgi:application --bind 0.0.0.0:$PORT

# Expose port 8000
EXPOSE 8888