#!/bin/bash
set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}  Настройка Video Generation Service${NC}"
echo -e "${GREEN}==================================================${NC}"

# 1. Создание директорий
echo -e "${YELLOW}Создаем необходимые директории...${NC}"
mkdir -p data/outputs data/huggingface_cache data/models

# 2. Проверка .env файла
echo -e "${YELLOW}Проверяем наличие .env файла...${NC}"
if [ ! -f .env ]; then
    echo -e "${RED}ВНИМАНИЕ: Файл .env не найден!${NC}"
    echo -e "${YELLOW}Создайте файл .env со следующими переменными:${NC}"
    echo ""
    cat << 'EOL'
S3_BUCKET_NAME=your-bucket-name
S3_REGION=eu-central-2
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
CUDA_VISIBLE_DEVICES=0
EOL
    echo ""
    read -p "Хотите создать шаблон .env сейчас? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat > .env << 'EOL'
# AWS S3 Configuration
S3_BUCKET_NAME=storage.modera.fashion
S3_REGION=eu-central-2
S3_ACCESS_KEY=
S3_SECRET_KEY=

# GPU Configuration
CUDA_VISIBLE_DEVICES=0
EOL
        echo -e "${GREEN}Файл .env создан. Пожалуйста, заполните AWS credentials.${NC}"
    fi
else
    echo -e "${GREEN}Файл .env найден.${NC}"
fi

# 3. Проверка установки Docker
echo -e "${YELLOW}Проверяем установку Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker не найден. Пожалуйста, установите Docker и перезапустите скрипт.${NC}"
    exit 1
fi
echo -e "${GREEN}Docker установлен.${NC}"

# 4. Проверка установки Docker Compose
echo -e "${YELLOW}Проверяем установку Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose не найден. Пожалуйста, установите Docker Compose и перезапустите скрипт.${NC}"
    exit 1
fi
echo -e "${GREEN}Docker Compose установлен.${NC}"

# 5. Проверка NVIDIA Docker
echo -e "${YELLOW}Проверяем NVIDIA Container Toolkit...${NC}"
if ! docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo -e "${RED}ВНИМАНИЕ: NVIDIA Container Toolkit не найден или не настроен!${NC}"
    echo -e "${YELLOW}Для работы с GPU необходимо установить NVIDIA Container Toolkit.${NC}"
    echo -e "${YELLOW}Инструкции: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html${NC}"
else
    echo -e "${GREEN}NVIDIA Container Toolkit настроен корректно.${NC}"
fi

# 6. Сборка и запуск контейнера
echo -e "${GREEN}Собираем и запускаем Docker контейнер...${NC}"
docker-compose up -d --build

# 7. Ожидание запуска
echo -e "${YELLOW}Ожидаем запуск сервиса (10 секунд)...${NC}"
sleep 10

# 8. Проверка статуса
echo -e "${YELLOW}Проверяем статус контейнера...${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}  Настройка завершена!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""
echo -e "${GREEN}Сервис запущен на порту 8000${NC}"
echo -e "${YELLOW}API endpoint: http://localhost:8000${NC}"
echo ""
echo -e "${YELLOW}Полезные команды:${NC}"
echo -e "  Просмотр логов:    ${GREEN}docker-compose logs -f${NC}"
echo -e "  Остановка:         ${GREEN}docker-compose down${NC}"
echo -e "  Перезапуск:        ${GREEN}docker-compose restart${NC}"
echo -e "  Проверка GPU:      ${GREEN}docker exec -it video-generation-api nvidia-smi${NC}"
echo "" 