# SkyReels-V2 Video Generation Docker Image
FROM nvidia/cuda:13.0.1-cudnn-devel-ubuntu24.04

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

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

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
