# ===============================================
# VIADOCS Backend - Full Production Setup for Railway
# ===============================================

# Use official Python lightweight image
FROM python:3.11-slim

# --- Install system dependencies required by all tools ---
RUN apt-get update && apt-get install -y \
    libreoffice \
    ghostscript \
    poppler-utils \
    g++ \
    libqpdf-dev \
    fonts-dejavu \
    ttf-mscorefonts-installer \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- Set environment variables for LibreOffice ---
ENV OOO_FORCE_DESKTOP=gnome
ENV HOME=/tmp

# --- Set working directory ---
WORKDIR /app

# --- Copy all project files into container ---
COPY . .

# --- Upgrade pip and install Python dependencies ---
RUN pip install --upgrade pip && pip install -r requirements.txt

# --- Expose Flask/Gunicorn port ---
EXPOSE 5000

# --- Start Gunicorn server (for Railway) ---
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]
