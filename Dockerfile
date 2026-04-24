# Dockerfile (root)

# ---- Base image -----------------------------------------------------------
# Use the official lightweight Python image that matches the project’s
# requirement (Python 3.13+).  The tag “slim‑bookworm” is small and includes
# the OS libraries needed for the HuggingFace embedding model.
FROM python:3.13-slim-bookworm AS base

# ---- Build stage -----------------------------------------------------------
# Install system‑level dependencies required by sentence‑transformers
# (the HuggingFace embedding model).  Keep the layer count low for fast builds.
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
RUN pip install --no-cache-dir -r requirements.txt

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