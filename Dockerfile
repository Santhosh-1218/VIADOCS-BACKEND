# ===============================================
# VIADOCS Backend - Stable & Fully Working Version
# ===============================================

FROM python:3.11-slim

# --- Install system tools and dependencies ---
RUN apt-get update && apt-get install -y \
    libreoffice \
    ghostscript \
    poppler-utils \
    g++ \
    libqpdf-dev \
    fonts-dejavu-core \
    fonts-liberation \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- Set environment variables for stability ---
ENV DEBIAN_FRONTEND=noninteractive
ENV OOO_FORCE_DESKTOP=gnome
ENV HOME=/tmp
ENV DISPLAY=:0
ENV LIBREOFFICE_HEADLESS=true
ENV PYTHONUNBUFFERED=1

# --- Working directory ---
WORKDIR /app

# --- Copy project files ---
COPY . .

# --- Install Python packages ---
RUN pip install --upgrade pip && pip install gunicorn && pip install -r requirements.txt

# --- Expose Flask port ---
EXPOSE 5000

# --- Health check (optional) ---
HEALTHCHECK CMD curl --fail http://localhost:${PORT:-5000}/api/health || exit 1

# --- Start Gunicorn (simplified for Railway) ---
CMD gunicorn app:app --bind 0.0.0.0:$PORT
