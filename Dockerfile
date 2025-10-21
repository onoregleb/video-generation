# SkyReels-V2 Video Generation Docker Image
FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    wget \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone SkyReels-V2 repository
RUN git clone https://github.com/SkyworkAI/SkyReels-V2.git

# Install build dependencies first
RUN pip3 install --no-cache-dir --break-system-packages packaging wheel setuptools ninja

# Copy requirements and install dependencies in stages
COPY requirements.txt .

# Stage 1: Install torch first (required for flash-attn compilation)
RUN pip3 install --no-cache-dir --break-system-packages torch==2.5.1 torchvision==0.20.1

# Stage 2: Install flash-attn (needs torch)
RUN pip3 install --no-cache-dir --break-system-packages flash-attn --no-build-isolation

# Stage 3: Install remaining dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt || true

# Copy application files
COPY skyreels_api.py .

# Create data directories
RUN mkdir -p /app/data/outputs /app/data/huggingface_cache

# Set environment variables for caching
ENV HF_HOME=/app/data/huggingface_cache
ENV TRANSFORMERS_CACHE=/app/data/huggingface_cache
ENV OUTPUT_BASE_DIR=/app/data/outputs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python3", "-m", "uvicorn", "skyreels_api:app", "--host", "0.0.0.0", "--port", "8000"]
