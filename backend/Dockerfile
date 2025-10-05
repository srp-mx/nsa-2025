# Use the official Python image from the Docker Hub
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev \
    libproj-dev proj-data proj-bin \
    libgeos-dev \
    #libatlas-base-dev liblapack-dev \
    libopenblas-dev liblapack-dev \
    libfreetype6-dev libpng-dev libjpeg-dev zlib1g-dev \
    libnetcdf-dev libhdf5-dev \
    curl git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


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
COPY --chown=appuser:appuser . /code/

# Expose the port the app runs on
EXPOSE 8000

# Run the application
ENTRYPOINT [ "/code/entrypoint.sh" ]
