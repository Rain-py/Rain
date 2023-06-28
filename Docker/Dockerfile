# Base image
FROM python:3.10-slim-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Install necessary system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libblas3 \
        liblapack3 \
        libopenblas-dev \
        liblapack-dev \
        libatlas-base-dev \
        gfortran \
    && rm -rf /var/lib/apt/lists/* /tmp/* ~/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt


# Remove unnecessary build dependencies
RUN apt-get remove -y --purge \
        build-essential \
        libopenblas-dev \
        liblapack-dev \
        libatlas-base-dev \
        gfortran \
    && apt-get autoremove -y --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* ~/*

# Set the entrypoint to accept the script path as an argument
ENTRYPOINT ["python"]

# Default command to print usage information
CMD ["-c", "print('You can run your script with: docker run -v /path/to/algo.py:/app/algo.py mostafaw/rain_worker:1.0.0 /app/algo.py')"]


