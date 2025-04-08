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

# Copy project files
COPY . /app/

# Run Django tests using pytest and coverage
# CMD ["python","manage.py", "migrate", "&&", "python", "manage.py", "collectstatic","&&", "uvicorn", "swaphub.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload"]
# ["uvicorn", "swaphub.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload"]



# Expose port 8000
EXPOSE 8888
