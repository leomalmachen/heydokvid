FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/backend/requirements-production.txt .
RUN pip install --no-cache-dir -r requirements-production.txt

# Copy all code
COPY . .

# Expose port
EXPOSE 10000

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=10000

# Run the application from the correct location
CMD ["python", "backend/backend/main.py"] 