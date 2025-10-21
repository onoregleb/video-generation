# API Examples - SkyReels-V2 Image-to-Video

Примеры использования упрощенного Image-to-Video API с поддержкой 540P и 720P разрешений.

## 📋 Содержание

- [Быстрый старт](#быстрый-старт)
- [Основные примеры](#основные-примеры)
- [Параметры запроса](#параметры-запроса)
- [Проверка статуса](#проверка-статуса)
- [Python клиент](#python-клиент)
- [Примеры использования](#примеры-использования)

## Быстрый старт

### Основной endpoint

```
POST /generate
```

### Минимальный пример (с дефолтным промптом)

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "image_url": "https://example.com/portrait.jpg",
    "resolution": "540P"
  }'
```

### С кастомным промптом

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "image_url": "https://example.com/portrait.jpg",
    "resolution": "540P",
    "prompt": "A beautiful woman touching her hair gracefully"
  }'
```

## Основные примеры

### 1. Image-to-Video 540P (рекомендуется)

Стандартное разрешение, требует ~24GB VRAM:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "image_url": "https://example.com/portrait.jpg",
    "resolution": "540P",
    "prompt": "A person looking at the camera with a gentle smile"
  }'
```

**Ответ:**
```json
{
  "process_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. Image-to-Video 720P (высокое качество)

Высокое разрешение, требует >60GB VRAM:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "image_url": "https://example.com/portrait.jpg",
    "resolution": "720P",
    "prompt": "A woman walking through a beautiful garden"
  }'
```

### 3. Автоматическое определение разрешения

API автоматически подгоняет изображение под выбранное разрешение:

- **540P**: 960x544 (горизонтальная) или 544x960 (вертикальная)
- **720P**: 1280x720 (горизонтальная) или 720x1280 (вертикальная)

Портретные изображения автоматически конвертируются в вертикальное видео, ландшафтные - в горизонтальное.

## Параметры запроса

### Обязательные параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `user_id` | string | ID пользователя для организации файлов |
| `image_url` | string (URL) | Ссылка на изображение (HTTP/HTTPS) |

### Опциональные параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `resolution` | string | `"540P"` | Разрешение: `"540P"` или `"720P"` |
| `prompt` | string | `"A cinematic video with smooth motion and natural movement"` | Описание желаемой анимации (опционально) |
| `num_frames` | int | `97` | Количество кадров (97 ≈ 4 сек при 24 FPS) |
| `fps` | int | `24` | Кадров в секунду |
| `guidance_scale` | float | `5.0` | Сила следования промпту (3.0-8.0) |
| `shift` | float | `5.0` | Параметр сдвига для генерации |
| `inference_steps` | int | `30` | Шагов инференса (больше = качественнее, но медленнее) |
| `seed` | int | `null` | Сид для воспроизводимости (генерируется автоматически) |
| `use_teacache` | bool | `true` | Ускорение генерации (рекомендуется) |
| `teacache_thresh` | float | `0.3` | Порог teacache (0.1-0.3) |
| `use_ret_steps` | bool | `true` | Retention steps для качества |
| `offload` | bool | `true` | CPU offloading для экономии VRAM |
| `process_id` | string | `null` | Кастомный ID процесса (генерируется автоматически) |

## Проверка статуса

### Запрос статуса

```bash
curl -X POST http://localhost:8000/status \
  -H "Content-Type: application/json" \
  -d '{
    "process_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Возможные статусы

**В очереди:**
```json
{
  "status": "queued",
  "user_id": "user123"
}
```

**В процессе:**
```json
{
  "status": "processing",
  "user_id": "user123",
  "message": "Generating video..."
}
```

**Завершено:**
```json
{
  "status": "done",
  "user_id": "user123",
  "video_url": "https://storage.modera.fashion/videos/user123/550e8400-e29b-41d4-a716-446655440000.mp4",
  "generation_time_seconds": 127.43,
  "message": "Video generation completed"
}
```

**Ошибка:**
```json
{
  "status": "failed",
  "user_id": "user123",
  "error": "Failed to load image",
  "generation_time_seconds": 12.5
}
```

## Python клиент

### Базовый пример

```python
import requests
import time

API_URL = "http://localhost:8000"

def generate_video(image_url, resolution="540P", prompt=None):
    """Генерация видео из изображения"""
    
    # Запуск генерации
    response = requests.post(
        f"{API_URL}/generate",
        json={
            "user_id": "python_client",
            "image_url": image_url,
            "resolution": resolution,
            "prompt": prompt  # None = использовать дефолтный промпт
        }
    )
    response.raise_for_status()
    process_id = response.json()["process_id"]
    print(f"✅ Задача создана: {process_id}")
    
    # Проверка статуса
    while True:
        status_response = requests.post(
            f"{API_URL}/status",
            json={"process_id": process_id}
        )
        status_response.raise_for_status()
        status = status_response.json()
        
        if status["status"] == "done":
            print(f"✅ Готово! Время: {status['generation_time_seconds']}s")
            print(f"🎥 Видео: {status['video_url']}")
            return status["video_url"]
        
        elif status["status"] == "failed":
            print(f"❌ Ошибка: {status.get('error')}")
            return None
        
        else:
            message = status.get("message", status["status"])
            print(f"⏳ {message}")
            time.sleep(5)

# Использование
if __name__ == "__main__":
    # С дефолтным промптом
    video_url = generate_video(
        image_url="https://example.com/portrait.jpg",
        resolution="540P"
    )
    
    # С кастомным промптом
    video_url = generate_video(
        image_url="https://example.com/portrait.jpg",
        resolution="720P",
        prompt="A beautiful woman touching her hair gracefully"
    )
```

### Продвинутый пример с параметрами

```python
import requests
import time

def generate_video_advanced(
    image_url,
    resolution="540P",
    prompt=None,
    num_frames=97,
    guidance_scale=5.0,
    fps=24,
    seed=None
):
    """Генерация с продвинутыми настройками"""
    
    payload = {
        "user_id": "advanced_user",
        "image_url": image_url,
        "resolution": resolution,
        "num_frames": num_frames,
        "guidance_scale": guidance_scale,
        "fps": fps,
        "use_teacache": True,
        "teacache_thresh": 0.3
    }
    
    # Добавляем опциональные параметры
    if prompt:
        payload["prompt"] = prompt
    if seed is not None:
        payload["seed"] = seed
    
    response = requests.post("http://localhost:8000/generate", json=payload)
    response.raise_for_status()
    
    process_id = response.json()["process_id"]
    print(f"Process ID: {process_id}")
    
    # Ожидание завершения
    while True:
        status_resp = requests.post(
            "http://localhost:8000/status",
            json={"process_id": process_id}
        )
        status = status_resp.json()
        
        if status["status"] == "done":
            return status["video_url"]
        elif status["status"] == "failed":
            raise Exception(status.get("error"))
        
        time.sleep(5)

# Пример использования
video_url = generate_video_advanced(
    image_url="https://example.com/portrait.jpg",
    resolution="540P",
    prompt="A model walking on a runway",
    num_frames=97,
    guidance_scale=6.0,
    fps=24,
    seed=42  # для воспроизводимости
)
print(f"Video: {video_url}")
```

## Примеры использования

### 1. Портретная анимация

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "portraits",
    "image_url": "https://example.com/model.jpg",
    "resolution": "540P",
    "prompt": "A professional model touching her hair, soft lighting, studio setting",
    "guidance_scale": 6.0
  }'
```

### 2. Fashion анимация

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "fashion",
    "image_url": "https://example.com/outfit.jpg",
    "resolution": "720P",
    "prompt": "A model wearing elegant dress, walking gracefully",
    "num_frames": 97,
    "fps": 24
  }'
```

### 3. Быстрая анимация (меньше кадров)

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "quick",
    "image_url": "https://example.com/person.jpg",
    "resolution": "540P",
    "num_frames": 49,
    "prompt": "A person smiling at the camera"
  }'
```

### 4. Без промпта (дефолтный)

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "default",
    "image_url": "https://example.com/image.jpg",
    "resolution": "540P"
  }'
```

## Информационные endpoints

### Получить информацию об API

```bash
curl http://localhost:8000/
```

**Ответ:**
```json
{
  "name": "SkyReels-V2 Image-to-Video API",
  "version": "2.0",
  "description": "Convert images to videos with 540P or 720P resolution",
  "status": "running",
  "supported_resolutions": ["540P", "720P"],
  "default_prompt": "A cinematic video with smooth motion and natural movement",
  "queue_size": 0
}
```

### Health check

```bash
curl http://localhost:8000/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "cuda_available": true,
  "cuda_devices": 1,
  "queue_size": 0
}
```

### Список всех процессов (debug)

```bash
curl http://localhost:8000/processes
```

## Советы и рекомендации

### Разрешения

- **540P (960x544)**: Рекомендуется для большинства случаев
  - Требует ~24GB VRAM
  - Быстрее генерируется
  - Хорошее качество

- **720P (1280x720)**: Для максимального качества
  - Требует >60GB VRAM
  - Медленнее генерируется
  - Отличное качество

### Оптимизация скорости

1. **Включайте teacache** (по умолчанию включен):
   ```json
   "use_teacache": true,
   "teacache_thresh": 0.3
   ```

2. **Используйте меньше шагов** для быстрой генерации:
   ```json
   "inference_steps": 20
   ```

3. **Включайте offload** при нехватке VRAM:
   ```json
   "offload": true
   ```

### Качество

1. **Увеличьте guidance_scale** для более точного следования промпту:
   ```json
   "guidance_scale": 6.0
   ```

2. **Больше шагов инференса**:
   ```json
   "inference_steps": 50
   ```

3. **Используйте детальные промпты**:
   ```json
   "prompt": "A professional model in elegant attire, touching her hair gracefully, studio lighting, high fashion photography style"
   ```

### Промпты

**Хорошие примеры промптов:**

- `"A beautiful woman touching her hair gracefully"`
- `"A model walking on a runway with confidence"`
- `"A person smiling at the camera with natural expression"`
- `"A fashion model in elegant pose, studio lighting"`
- `"A cinematic portrait with smooth natural movement"`

**Дефолтный промпт** (если не указан):
- `"A cinematic video with smooth motion and natural movement"`

## Troubleshooting

### CUDA Out of Memory

Если получаете ошибку нехватки VRAM:

1. Используйте 540P вместо 720P
2. Убедитесь что `offload: true`
3. Уменьшите `num_frames`
4. Закройте другие приложения использующие GPU

### Медленная генерация

1. Убедитесь что `use_teacache: true`
2. Уменьшите `inference_steps` до 20-25
3. Используйте `teacache_thresh: 0.3` для максимального ускорения

### Ошибка загрузки изображения

Убедитесь что:
- URL доступен публично
- Формат изображения: JPG, PNG, WEBP
- Размер изображения адекватен (не слишком большой)

## Системные требования

### Для 540P
- GPU: NVIDIA с 24GB+ VRAM (рекомендуется RTX 4090 или A6000)
- RAM: 32GB+
- Место на диске: 50GB+

### Для 720P
- GPU: NVIDIA с 60GB+ VRAM (рекомендуется A100 80GB)
- RAM: 64GB+
- Место на диске: 50GB+

## Примеры cURL команд

### Полная команда с всеми параметрами

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "full_example",
    "image_url": "https://example.com/portrait.jpg",
    "resolution": "540P",
    "prompt": "A beautiful woman touching her hair gracefully",
    "num_frames": 97,
    "guidance_scale": 5.0,
    "shift": 5.0,
    "inference_steps": 30,
    "fps": 24,
    "seed": 42,
    "use_teacache": true,
    "teacache_thresh": 0.3,
    "use_ret_steps": true,
    "offload": true
  }'
```

### Сохранение process_id в переменную

```bash
# Создание задачи
PROCESS_ID=$(curl -s -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "image_url": "https://example.com/portrait.jpg",
    "resolution": "540P"
  }' | jq -r '.process_id')

echo "Process ID: $PROCESS_ID"

# Проверка статуса
curl -X POST http://localhost:8000/status \
  -H "Content-Type: application/json" \
  -d "{\"process_id\": \"$PROCESS_ID\"}"
```

## Дополнительная информация

Для получения дополнительной информации:

- [README.md](README.md) - основная документация
- [QUICKSTART.md](QUICKSTART.md) - быстрый старт
- [DOCKER_CLEANUP.md](DOCKER_CLEANUP.md) - управление Docker
- Официальный репозиторий: [SkyReels-V2](https://github.com/Skywork-AI/SkyReels-V2)
