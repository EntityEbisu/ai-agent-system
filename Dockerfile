# Dockerfile (root)

# ---- Base image -----------------------------------------------------------
# Use the official lightweight Python 3.11 image.
# Python 3.11 is pinned for compatibility with sentence-transformers
# and to avoid GPU-package overhead on CPU-only deployments.
FROM python:3.11-slim-bookworm AS base

# ---- Build stage -----------------------------------------------------------
# Install system‑level dependencies required by sentence-transformers
# (the HuggingFace embedding model) and PyTorch CPU build.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Create a non‑root user (security best practice)
ARG UID=1000
ARG GID=1000
RUN addgroup --gid $GID appuser && \
    adduser --uid $UID --gid $GID --disabled-password --gecos "" appuser

# Set working directory
WORKDIR /app

# ---- Install Python dependencies -------------------------------------------
COPY requirements.txt .
# Install CPU-only PyTorch first to avoid pulling GPU packages
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# ---- Copy application code -------------------------------------------------
COPY . .

# Change ownership to the non‑root user
RUN chown -R appuser:appuser /app

# ---- Runtime --------------------------------------------------------------
USER appuser

# Expose the FastAPI port (default in `app/main.py` is 8000)
EXPOSE 8000

# Entrypoint – start the server in reload mode for development or without it
# for production.  The CI/CD pipeline can override the command if needed.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]