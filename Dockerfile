FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create data directory
RUN mkdir -p /app/data/papers /app/data/temp_uploads

# Set Python path
ENV PYTHONPATH=/app

# Expose Streamlit port
EXPOSE 8501

# Default command (can be overridden in docker-compose)
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.address", "0.0.0.0"]
