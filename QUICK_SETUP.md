# 🚀 Быстрая установка

## Для нового проекта

```bash
# 1. Клонировать репозиторий
git clone <your-repo>
cd Sky

# 2. Создать .env
cp env.example .env
nano .env  # Добавьте ваши S3 credentials

# 3. Создать директории
mkdir -p data/outputs data/huggingface_cache

# 4. Запустить
docker-compose up -d --build

# 5. Проверить
curl http://localhost:8000/health
```

## Для обновления существующего проекта

```bash
# 1. Остановить текущий сервис
docker-compose down

# 2. Создать резервную копию (опционально)
tar -czf backup_$(date +%Y%m%d).tar.gz data/ .env

# 3. Обновить код (git pull или скачать файлы)
git pull origin main

# 4. Удалить старые файлы (см. CLEANUP_INSTRUCTIONS.md)
rm -rf SkyReels-V1/ v2_res/
rm task.sh setup.sh video_generate_v2.py test_image_crop.py

# 5. Очистить Docker
docker system prune -a

# 6. Запустить новую версию
docker-compose up -d --build

# 7. Проверить
docker-compose logs -f
```

## Быстрый тест

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "model_id": "Skywork/SkyReels-V2-I2V-14B-540P",
    "prompt": "A beautiful woman touches her hair",
    "image_url": "https://example.com/test.jpg"
  }'
```

curl -X POST http://localhost:8000/generate   -H "Content-Type: application/json"   -d '{
    "user_id": "test_user",
    "image_url": "https://i.pinimg.com/736x/70/11/d1/7011d1242b1e366041e42d662225fb20.jpg",
    "resolution": "540P",
    "prompt": "A beautiful woman touches her hair"
  }'

## 📖 Полная документация

- [README.md](README.md) - Основная документация
- [API_EXAMPLES.md](API_EXAMPLES.md) - Примеры API
- [DOCKER_CLEANUP.md](DOCKER_CLEANUP.md) - Очистка Docker
- [MIGRATION_NOTES.md](MIGRATION_NOTES.md) - Заметки по миграции

