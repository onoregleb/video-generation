# 🚀 Quick Start Guide - Image-to-Video API

Быстрый старт для SkyReels-V2 Image-to-Video API.

## Prerequisites
- NVIDIA GPU with 24GB+ VRAM (RTX 4090, A100, etc.)
- NVIDIA Container Toolkit installed
- Docker & Docker Compose installed
- AWS S3 bucket or S3-compatible storage

## Step 1: Configure Environment

Create `.env` file:
```bash
cat > .env << 'EOF'
S3_BUCKET_NAME=your-bucket-name
S3_REGION=eu-central-2
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
CUDA_VISIBLE_DEVICES=0
EOF
```

## Step 2: Create Data Directories

```bash
mkdir -p data/outputs data/huggingface_cache
```

## Step 3: Launch Service

```bash
# Build and start the container
docker-compose up -d --build

# View logs
docker-compose logs -f
```

The API will be available at `http://localhost:8000`

## Step 4: Test API

### Generate Video (Minimal Example)

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "image_url": "https://example.com/portrait.jpg",
    "resolution": "540P"
  }'
```

**Response:**
```json
{"process_id": "550e8400-e29b-41d4-a716-446655440000"}
```

### Generate Video with Custom Prompt

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "image_url": "https://example.com/portrait.jpg",
    "resolution": "540P",
    "prompt": "A beautiful woman touching her hair gracefully"
  }'
```

### Check Status

```bash
curl -X POST http://localhost:8000/status \
  -H "Content-Type: application/json" \
  -d '{"process_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

**Response (Queued):**
```json
{
  "status": "queued",
  "user_id": "test_user"
}
```

**Response (Processing):**
```json
{
  "status": "processing",
  "user_id": "test_user",
  "message": "Generating video..."
}
```

**Response (Done):**
```json
{
  "status": "done",
  "user_id": "test_user",
  "video_url": "https://storage.modera.fashion/videos/test_user/550e8400-e29b-41d4-a716-446655440000.mp4",
  "generation_time_seconds": 127.43,
  "message": "Video generation completed"
}
```

## Python Client Example

```python
import requests
import time

API_URL = "http://localhost:8000"

def generate_video(image_url, resolution="540P", prompt=None):
    # Start generation
    response = requests.post(
        f"{API_URL}/generate",
        json={
            "user_id": "test_user",
            "image_url": image_url,
            "resolution": resolution,
            "prompt": prompt
        }
    )
    process_id = response.json()["process_id"]
    print(f"✅ Process started: {process_id}")
    
    # Poll status
    while True:
        status_resp = requests.post(
            f"{API_URL}/status",
            json={"process_id": process_id}
        )
        status = status_resp.json()
        
        if status["status"] == "done":
            print(f"✅ Done! Video: {status['video_url']}")
            return status["video_url"]
        elif status["status"] == "failed":
            print(f"❌ Failed: {status.get('error')}")
            return None
        else:
            print(f"⏳ {status.get('message', status['status'])}")
            time.sleep(5)

# Usage
video_url = generate_video(
    image_url="https://example.com/portrait.jpg",
    resolution="540P",
    prompt="A woman touching her hair gracefully"
)
```

## Monitoring

### View Logs
```bash
docker-compose logs -f
```

### Check GPU Usage
```bash
docker exec -it skyreels-v2-api nvidia-smi
```

### Check API Health
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "cuda_available": true,
  "cuda_devices": 1,
  "queue_size": 0
}
```

### Get API Info
```bash
curl http://localhost:8000/
```

**Response:**
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

## Troubleshooting

### GPU not detected
```bash
# Test NVIDIA drivers
nvidia-smi

# Test NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### S3 upload fails
- Verify AWS credentials in `.env`
- Check bucket permissions (needs `s3:PutObject`)
- Ensure bucket exists in specified region

### Out of memory (CUDA OOM)
Use 540P resolution (not 720P):
```json
{
  "resolution": "540P"
}
```

Or reduce frames:
```json
{
  "num_frames": 49
}
```

### First run is slow
The first run downloads the model (~20-30GB). Subsequent runs are faster as models are cached.

## Resolution Guide

### 540P (Recommended)
- **Dimensions**: 960x544 (landscape) or 544x960 (portrait)
- **VRAM**: ~24GB
- **Generation time**: 3-5 minutes
- **Use case**: Most projects, fast iteration

### 720P (High Quality)
- **Dimensions**: 1280x720 (landscape) or 720x1280 (portrait)
- **VRAM**: >60GB
- **Generation time**: 5-8 minutes
- **Use case**: Final high-quality output

## Architecture

```
Client → POST /generate → Queue → Load Image → Resize → Generate Video → Upload S3 → Return URL
                                       ↓
                                  Auto-resize based on resolution
                                  (Portrait/Landscape detection)
```

- **Queue**: Sequential processing (1 GPU)
- **Generation time**: 3-5 minutes (540P), 5-8 minutes (720P)
- **GPU memory**: 24GB (540P), 60GB+ (720P)
- **Image resizing**: Automatic based on resolution

## Tips for Best Results

### Prompts
- Use descriptive prompts for better control
- Default prompt works well for general animations
- Examples:
  - `"A beautiful woman touching her hair gracefully"`
  - `"A model walking on a runway with confidence"`
  - `"A person smiling at the camera with natural expression"`

### Image Quality
- Use high-resolution images (at least 1024px)
- Clear subject, good lighting
- Portrait or landscape orientation both work

### Performance
- Enable teacache (default: enabled) for 40% speed boost
- Use 540P for faster iteration
- Reduce `num_frames` for shorter videos

## Next Steps

- See [API_EXAMPLES.md](API_EXAMPLES.md) for more examples
- See [README.md](README.md) for full documentation
- See [DOCKER_CLEANUP.md](DOCKER_CLEANUP.md) for Docker maintenance

---

**API готов к использованию!** 🎉
