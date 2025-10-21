FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    wget \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY server_cloud.py task.sh requirements.txt ./
COPY SkyReels-V1 ./SkyReels-V1

# Установка Python зависимостей для API сервера
RUN pip3 install --no-cache-dir -r requirements.txt

# Установка PyTorch с поддержкой CUDA 12.1
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Установка зависимостей для SkyReels-V1
RUN pip3 install --no-cache-dir -r SkyReels-V1/requirements.txt

# Создание необходимых директорий
RUN mkdir -p /mnt/tank/scratch/edubskiy/outputs \
    /mnt/tank/scratch/edubskiy/public_videos \
    /mnt/tank/scratch/edubskiy/huggingface_cache

# Делаем task.sh исполняемым
RUN chmod +x task.sh

# Expose API port
EXPOSE 8000

# Запуск API сервера
CMD ["uvicorn", "server_cloud:app", "--host", "0.0.0.0", "--port", "8000"] 