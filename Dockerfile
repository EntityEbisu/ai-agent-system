# Dockerfile – single-stage, CPU-only build
#
# Strategy:
#   1. Install CPU-only PyTorch from the official CPU-only index.
#   2. Install all other dependencies via requirements.txt.
#   3. The requirements.txt does NOT list torch (it's installed in step 1),
#      preventing pip from pulling the GPU bundle (nvidia-*, triton).
#   4. Remove the nvidia-* packages that onnxruntime (chromadb dep) pulls in
#      as optional CUDA libraries — they're never loaded on a CPU-only host.

FROM python:3.11-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
ARG UID=1000
ARG GID=1000
RUN addgroup --gid $GID appuser && \
    adduser --uid $UID --gid $GID --disabled-password --gecos "" appuser

WORKDIR /app

# Install CPU-only PyTorch from the official CPU-only index
RUN pip install --no-cache-dir torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Remove CUDA packages that onnxruntime (chromadb dep) pulls in but never uses
# on a CPU-only machine.  This reclaims ~2 GB.  triton is also GPU-only.
RUN pip uninstall -y \
    nvidia-cublas-cu12 nvidia-cuda-cupti-cu12 nvidia-cuda-nvrtc-cu12 \
    nvidia-cuda-runtime-cu12 nvidia-cudnn-cu12 nvidia-cufft-cu12 \
    nvidia-curand-cu12 nvidia-cusolver-cu12 nvidia-cusparse-cu12 \
    nvidia-cusparselt-cu12 nvidia-nccl-cu12 nvidia-nvjitlink-cu12 \
    nvidia-nvtx-cu12 triton \
    2>/dev/null || true

# Copy application code
COPY . .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
