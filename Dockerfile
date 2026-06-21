# Dockerfile – single-stage, CPU-only build
FROM python:3.11-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        && \
    rm -rf /var/lib/apt/lists/*

ARG UID=1000
ARG GID=1000
RUN addgroup --gid $GID appuser && \
    adduser --uid $UID --gid $GID --disabled-password --gecos "" appuser

WORKDIR /app

# ---- Stage: Install CPU-only PyTorch ----
RUN pip install --no-cache-dir torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python deps from CPU index too, so torch stays CPU-only
# (sentence-transformers → torch dep must resolve to the CPU variant)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
      --index-url https://download.pytorch.org/whl/cpu \
      --extra-index-url https://pypi.org/simple && \
    # Remove nvidia CUDA packages (not needed on CPU)
    pip uninstall -y \
        nvidia-cublas-cu12 nvidia-cuda-cupti-cu12 nvidia-cuda-nvrtc-cu12 \
        nvidia-cuda-runtime-cu12 nvidia-cudnn-cu12 nvidia-cufft-cu12 \
        nvidia-curand-cu12 nvidia-cusolver-cu12 nvidia-cusparse-cu12 \
        nvidia-cusparselt-cu12 nvidia-nccl-cu12 nvidia-nvjitlink-cu12 \
        nvidia-nvtx-cu12 \
        2>/dev/null || true && \
    # Remove GPU-only triton compiler
    pip uninstall -y triton 2>/dev/null || true && \
    # Strip caches, tests from installed packages (keep .dist-info for metadata)
    find /usr/local/lib/python3.11/site-packages -type d \( \
        -name "__pycache__" -o \
        -name "tests" -o \
        -name "test" \
    \) -exec rm -rf {} + 2>/dev/null || true && \
    # Remove native code .o / .a / .lib files and CMake artifacts
    find /usr/local/lib/python3.11/site-packages -type f \( \
        -name "*.o" -o -name "*.a" -o -name "*.lib" -o \
        -name "CMakeCache.txt" -o -name "cmake_install.cmake" \
    \) -delete 2>/dev/null || true && \
    # Remove huggingface model cache
    rm -rf /root/.cache /root/.local /tmp/*

# ---- Copy application code ----
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
