# Use the official Python image from the Docker Hub
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /code

# Create volumes for database and media files
VOLUME ["/code/config.yaml", "/code/media"]

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client &&\
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user with UID 1000
RUN adduser --disabled-password --gecos '' --uid 1000 appuser

# Change ownership of the work directory
RUN chown -R appuser /code

# Switch to the non-root user
USER appuser

# Install dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /code/

# Expose the port the app runs on
EXPOSE 8000

# Run the application
ENTRYPOINT [ "/code/entrypoint.sh" ]
