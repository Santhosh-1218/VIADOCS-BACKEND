# Use official lightweight Python image
FROM python:3.11-slim

# Install system dependencies required by PikePDF and other PDF tools
RUN apt-get update && apt-get install -y \
    g++ \
    libqpdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Start Gunicorn server
CMD ["gunicorn", "app:app"]
