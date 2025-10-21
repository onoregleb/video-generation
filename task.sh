#!/bin/bash
set -e

# Получаем параметры из переменных окружения
USER_ID=${USER_ID:-"default_user"}
MODEL_IMAGE=${MODEL_IMAGE:-"Skywork/SkyReels-V2-I2V-14B-540P"}
PROMPT=${PROMPT:-"Default prompt for video generation"}
IMAGE_PATH=${IMAGE_PATH:-"asia_try.png"}
PROCESS_ID=${PROCESS_ID:-"test_process"}

# Создаем директорию для результатов
OUTPUT_BASE_DIR=${OUTPUT_BASE_DIR:-"/mnt/tank/scratch/edubskiy/outputs"}
OUTPUT_DIR="${OUTPUT_BASE_DIR}/${USER_ID}/${PROCESS_ID}"
mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "Запуск генерации видео"
echo "=========================================="
echo "User ID: $USER_ID"
echo "Process ID: $PROCESS_ID"
echo "Модель: $MODEL_IMAGE"
echo "Изображение: $IMAGE_PATH"
echo "Промпт: $PROMPT"
echo "Выходная директория: $OUTPUT_DIR"
echo "=========================================="

# Настройка HuggingFace cache
export HF_HOME=${HF_HOME:-"/mnt/tank/scratch/edubskiy/huggingface_cache"}
export TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE:-$HF_HOME}
mkdir -p $HF_HOME

# Проверка наличия Python и pip
echo "Проверка Python окружения..."
python3 --version
pip3 --version

# Проверка версии Torch и доступности CUDA
echo "Проверка PyTorch и CUDA..."
python3 -c "import torch; print(f'PyTorch версия: {torch.__version__}'); print(f'CUDA доступна: {torch.cuda.is_available()}'); print(f'CUDA устройств: {torch.cuda.device_count()}' if torch.cuda.is_available() else 'GPU не найдено')" || {
    echo "ОШИБКА: PyTorch не установлен или некорректно настроен!"
    exit 1
}

# Фиксация времени начала
START_TIME=$(date +%s)
echo "Время начала: $(date)"

# Создаем файл статуса "processing"
STATUS_FILE="${OUTPUT_DIR}/status.json"
echo "{\"status\": \"processing\", \"process_id\": \"$PROCESS_ID\", \"message\": \"Video generation started\"}" > "$STATUS_FILE"

# Запуск генерации видео
echo "Запуск генерации видео..."
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

cd /app/SkyReels-V1

python3 video_generate.py \
  --model_id "${MODEL_IMAGE}" \
  --image "${IMAGE_PATH}" \
  --task_type i2v \
  --height 544 \
  --width 960 \
  --num_frames 97 \
  --guidance_scale 5.0 \
  --fps 24 \
  --offload \
  --prompt "${PROMPT}" \
  --seed 42 \
  --num_inference_steps 10 \
  --video_num 1 \
  --outdir "${OUTPUT_DIR}" || {
    echo "ОШИБКА: Генерация видео завершилась с ошибкой!"
    echo "{\"status\": \"failed\", \"error\": \"Video generation script failed\", \"process_id\": \"$PROCESS_ID\"}" > "$STATUS_FILE"
    exit 1
}

END_TIME=$(date +%s)
ELAPSED_TIME=$((END_TIME - START_TIME))

echo "=========================================="
echo "Генерация завершена"
echo "Общее время выполнения: $(($ELAPSED_TIME / 60)) минут $(($ELAPSED_TIME % 60)) секунд"
echo "=========================================="

# Проверка результата
echo "Содержимое выходной директории:"
ls -la "${OUTPUT_DIR}"

# Ищем mp4 файл в директории
VIDEO_PATH=$(find "${OUTPUT_DIR}" -maxdepth 1 -name "*.mp4" -type f | head -n 1)

if [ -n "$VIDEO_PATH" ]; then
  echo "✅ Видео успешно создано: $VIDEO_PATH"
  
  # Записываем успешный статус
  echo "{\"status\": \"done\", \"video_url\": \"$VIDEO_PATH\", \"process_id\": \"$PROCESS_ID\", \"ready_for_s3\": true}" > "$STATUS_FILE"
  
  echo "=========================================="
  echo "Видео готово к загрузке в S3"
  echo "=========================================="
else
  echo "❌ ОШИБКА: Видеофайл не найден в директории ${OUTPUT_DIR}"
  echo "{\"status\": \"failed\", \"error\": \"Video file not found after generation\", \"process_id\": \"$PROCESS_ID\"}" > "$STATUS_FILE"
  exit 1
fi 