# Changelog - Refactoring to AWS Direct Execution

## Дата: 2025-10-19

## Основные изменения

### ❌ Удалено
1. **SSH подключение** - больше не используется удаленное выполнение через SSH
2. **SLURM интеграция** - убраны все команды и функции для работы с SLURM
3. **Paramiko** - удалена зависимость для SSH
4. **SSH keys монтирование** - убрано из docker-compose.yml
5. **Conda окружение** - заменено на использование системного Python с pip

### ✅ Добавлено
1. **Прямое выполнение** - видео генерируется локально внутри Docker контейнера
2. **Python requests** - скачивание изображений через requests вместо wget
3. **Subprocess execution** - task.sh запускается напрямую через subprocess
4. **Улучшенная обработка ошибок** - более информативные сообщения об ошибках
5. **Документация** - обновлены README, добавлен QUICKSTART

### 🔄 Изменено

#### `server_cloud.py`
- Удалены функции:
  - `connect_to_itmo_server()` - SSH подключение
  - `create_slurm_script()` - создание SLURM скриптов
  - `check_job_status()` - проверка статуса SLURM задания
  - `download_and_upload_to_s3()` - промежуточная функция
  
- Изменены функции:
  - `download_image()` - теперь использует `requests` вместо `wget`
  - `run_video_generation()` - прямой запуск через `subprocess.run()`
  - Удалена логика ветвления `IS_LOCAL_MODE` vs SSH
  
- Переменные окружения:
  ```python
  # Удалено:
  - ITMO_SERVER_HOST, ITMO_SERVER_PORT, ITMO_SERVER_USERNAME
  - ITMO_SERVER_PASSWORD, ITMO_SERVER_KEY_PATH
  - IS_LOCAL_MODE, SLURM_*
  
  # Добавлено/изменено:
  - SCRIPT_PATH (путь к task.sh)
  ```

#### `task.sh`
- Удалено:
  - Все блоки с Conda (инициализация, создание окружения, активация)
  - Проверка и установка torch через conda
  - Установка зависимостей из requirements.txt
  - SLURM специфичные настройки
  
- Изменено:
  - Упрощенная проверка Python окружения
  - Прямой вызов `python3 video_generate.py` из `/app/SkyReels-V1`
  - Улучшенное логирование с эмодзи (✅/❌)
  
#### `Dockerfile`
- Удалено:
  - `openssh-client` - больше не нужен SSH
  - SSH директория `/root/.ssh`
  - `paramiko` установка
  
- Добавлено:
  - Копирование `SkyReels-V1/` директории
  - Установка зависимостей из `SkyReels-V1/requirements.txt`
  - Сделать `task.sh` исполняемым

#### `docker-compose.yml`
- Удалено:
  - Монтирование `/usr/bin/sbatch`, `/usr/bin/squeue`, `/usr/bin/sacct`
  - Монтирование `./ssh_keys:/root/.ssh`
  - `PUBLIC_VIDEOS_DIR` переменная окружения
  - `ITMO_SERVER_*` переменные
  
- Изменено:
  - `CUDA_VISIBLE_DEVICES` теперь настраивается через `.env` (по умолчанию 0)
  - Упрощенная структура volumes

#### `requirements.txt`
- Удалено:
  - `paramiko>=2.7.0`

#### `README.md`
- Полностью переписан для AWS EC2 + Direct Execution архитектуры
- Добавлена секция Architecture
- Обновлены примеры API
- Добавлена секция Troubleshooting
- Добавлена информация о Performance

#### `setup.sh`
- Удалена логика копирования SSH ключей
- Добавлена проверка `.env` файла
- Добавлена проверка NVIDIA Container Toolkit
- Улучшенный UI с цветами и структурированным выводом

## Новый Workflow

### Старый (через SLURM):
```
Client → API → SSH → SLURM → Queue → Conda Env → Generate → Check Status → Download → S3
```

### Новый (прямое выполнение):
```
Client → API → Queue → Download Image → Generate (local) → S3 Upload → Return URL
```

## Как это работает сейчас

1. **Клиент отправляет запрос** на `/run` с `image_url` и `prompt`
2. **Запрос добавляется в очередь** (threading.Queue) для последовательной обработки
3. **Воркер обрабатывает задачу**:
   - Скачивает изображение через Python `requests`
   - Запускает `task.sh` через `subprocess.run()` с переменными окружения
4. **task.sh выполняется**:
   - Создает выходную директорию
   - Запускает `SkyReels-V1/video_generate.py`
   - Создает `status.json` с результатом
5. **После генерации**:
   - Видео загружается в S3 напрямую
   - Статус обновляется на "done" с URL S3
6. **Клиент проверяет статус** через `/status` и получает ссылку на видео

## Требования к окружению

### AWS EC2:
- Инстанс с GPU (g5.xlarge, g5.2xlarge, p3.2xlarge и т.д.)
- NVIDIA Container Toolkit установлен
- Docker & Docker Compose установлены

### GPU:
- Минимум 12GB VRAM (рекомендуется 16GB+)
- CUDA 12.1 compatible

### S3:
- Bucket создан
- IAM роль или ключи с правами `s3:PutObject`

## Миграция

Если у вас был запущен старый код:

```bash
# 1. Остановите старый контейнер
docker-compose down

# 2. Обновите код
git pull

# 3. Создайте .env файл (см. QUICKSTART.md)

# 4. Пересоберите контейнер
./setup.sh
```

## Проверка

После запуска проверьте:

```bash
# 1. Контейнер запущен
docker-compose ps

# 2. GPU доступен
docker exec -it video-generation-api nvidia-smi

# 3. API отвечает
curl http://localhost:8000/processes

# 4. Тестовая генерация (см. QUICKSTART.md)
```

## Известные ограничения

1. **Очередь в памяти** - при перезапуске контейнера очередь теряется
2. **Статусы в памяти** - нет персистентного хранилища статусов
3. **Одна задача за раз** - очередь обрабатывает задачи последовательно
4. **Timeout 1 час** - если генерация превышает 1 час, задача завершается с ошибкой

## Будущие улучшения

- [ ] Redis/PostgreSQL для хранения статусов
- [ ] Celery для распределенной обработки
- [ ] WebSocket для real-time обновлений статуса
- [ ] Health check endpoint
- [ ] Metrics (Prometheus)
- [ ] Multiple GPU support

