FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install schedule requests

# Copy scripts
COPY scripts/ /app/scripts/

# Set python path to include scripts
ENV PYTHONPATH=/app/scripts

CMD ["python", "scripts/run_scraper.py"]
