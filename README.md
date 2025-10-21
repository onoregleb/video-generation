# SkyReels-V2 Image-to-Video API

Production-ready Docker-based Image-to-Video service using **SkyReels-V2**. Simplified API for converting images to videos with 540P and 720P resolution support.

## 🌟 Features

- **State-of-the-art** Image-to-Video generation using SkyReels-V2
- **Automatic image resizing** based on selected resolution
- **540P and 720P** resolution support
- **Optional prompts** - use default or provide custom prompts
- **Direct diffusers integration** - no shell scripts required
- **GPU-accelerated** with CUDA support
- **AWS S3 integration** for video storage
- **Queue-based processing** for multiple concurrent requests
- **Docker containerization** for easy deployment
- **RESTful API** with FastAPI

## 📋 Prerequisites

- Docker & Docker Compose
- NVIDIA GPU with CUDA support (12.1+)
- NVIDIA Container Toolkit
- AWS S3 bucket (or S3-compatible storage)
- Minimum 50GB GPU RAM for 14B models

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone <your-repo-url>
cd Sky

# Create .env file from example
cp env.example .env
# Edit .env with your S3 credentials
```

### 2. Configure Environment

Edit `.env` file:

```bash
S3_BUCKET_NAME=your-bucket-name
S3_REGION=eu-central-2
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
CUDA_VISIBLE_DEVICES=0
```

### 3. Create Data Directories

```bash
mkdir -p data/outputs data/huggingface_cache
```

### 4. Build and Run

```bash
# Build and start the container
docker-compose up -d --build

# View logs
docker-compose logs -f
```

The API will be available at `http://localhost:8000`

## 📖 API Documentation

### Generate Video from Image

**Endpoint:** `POST /generate`

**Minimal Example (with default prompt):**

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "image_url": "https://example.com/portrait.jpg",
    "resolution": "540P"
  }'
```

**Example with Custom Prompt:**

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

**720P High Quality Example:**

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "image_url": "https://example.com/portrait.jpg",
    "resolution": "720P",
    "prompt": "A model walking on a runway with confidence",
    "num_frames": 97,
    "fps": 24
  }'
```

**Response:**

```json
{
  "process_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Request Parameters

#### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | User identifier for organizing files |
| `image_url` | string | URL of input image (HTTP/HTTPS) |

#### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resolution` | string | `"540P"` | Resolution: `"540P"` or `"720P"` |
| `prompt` | string | `"A cinematic video with smooth motion and natural movement"` | Description of desired animation (optional) |
| `num_frames` | int | `97` | Number of frames (97 ≈ 4 sec @ 24 FPS) |
| `fps` | int | `24` | Frames per second |
| `guidance_scale` | float | `5.0` | Guidance scale (3.0-8.0) |
| `shift` | float | `5.0` | Shift parameter for generation |
| `inference_steps` | int | `30` | Inference steps (more = better quality, slower) |
| `seed` | int | `null` | Random seed (auto-generated if not provided) |
| `use_teacache` | bool | `true` | Speed optimization (recommended) |
| `teacache_thresh` | float | `0.3` | Teacache threshold (0.1-0.3) |
| `use_ret_steps` | bool | `true` | Retention steps for quality |
| `offload` | bool | `true` | CPU offloading to save VRAM |

### Automatic Image Resizing

The API automatically resizes images based on the selected resolution:

- **540P**: 960x544 (landscape) or 544x960 (portrait)
- **720P**: 1280x720 (landscape) or 720x1280 (portrait)

Portrait images are automatically converted to vertical videos, landscape images to horizontal videos.

### Supported Resolutions

| Resolution | Dimensions | VRAM Required | Use Case |
|------------|------------|---------------|----------|
| **540P** | 960x544 | ~24GB | Recommended for most cases |
| **720P** | 1280x720 | >60GB | High quality output |

### Check Status

**Endpoint:** `POST /status`

```bash
curl -X POST http://localhost:8000/status \
  -H "Content-Type: application/json" \
  -d '{"process_id": "your-process-id"}'
```

**Response (Processing):**

```json
{
  "status": "processing",
  "user_id": "user123",
  "message": "Generating video..."
}
```

**Response (Completed):**

```json
{
  "status": "done",
  "user_id": "user123",
  "video_url": "https://your-bucket.s3.region.amazonaws.com/videos/user123/process-id.mp4",
  "generation_time_seconds": 245.67
}
```

**Response (Failed):**

```json
{
  "status": "failed",
  "user_id": "user123",
  "error": "Error description",
  "generation_time_seconds": 30.5
}
```

### Health Check

**Endpoint:** `GET /health`

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

### List All Processes (Debug)

**Endpoint:** `GET /processes`

```bash
curl http://localhost:8000/processes
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `S3_BUCKET_NAME` | - | AWS S3 bucket name (required) |
| `S3_REGION` | `eu-central-2` | AWS S3 region |
| `S3_ACCESS_KEY` | - | AWS access key (required) |
| `S3_SECRET_KEY` | - | AWS secret key (required) |
| `S3_ENDPOINT_URL` | - | S3-compatible endpoint (optional) |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU device ID |
| `HF_HOME` | `/app/data/huggingface_cache` | HuggingFace cache directory |
| `OUTPUT_BASE_DIR` | `/app/data/outputs` | Temporary output directory |

### GPU Requirements

| Resolution | VRAM Required | Recommended GPU |
|-----------|---------------|----------------|
| 540P | ~24GB | RTX 4090, A100-40GB, A6000 |
| 720P | >60GB | A100-80GB, H100 |

## 🐳 Docker Management

### View Logs

```bash
docker-compose logs -f
```

### Stop Container

```bash
docker-compose down
```

### Restart Container

```bash
docker-compose restart
```

### Rebuild Container

```bash
docker-compose up -d --build
```

### Check GPU in Container

```bash
docker exec -it skyreels-v2-api nvidia-smi
```

### Cleanup Docker Cache

```bash
# Remove all unused Docker resources
docker system prune -a

# For detailed cleanup commands, see DOCKER_CLEANUP.md
```

📖 **See [DOCKER_CLEANUP.md](DOCKER_CLEANUP.md) for comprehensive Docker cleanup guide**

## 📊 Performance

### Generation Times (with teacache)

- **540P (97 frames)**: ~3-5 minutes on H100/A100
- **720P (97 frames)**: ~5-8 minutes on H100/A100
- **First run**: +5-10 minutes for model download

### Optimization

- **Teacache**: Enabled by default, reduces inference time by ~40%
- **CPU Offload**: Enabled by default, reduces VRAM usage
- **Resolution**: Use 540P for faster generation
- **Inference Steps**: Reduce to 20-25 for faster (slightly lower quality)

## 🛠️ Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA drivers
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Out of Memory

- Use 540P instead of 720P
- Reduce `num_frames` (e.g., 49 instead of 97)
- Ensure `offload: true` (enabled by default)
- Reduce `inference_steps` to 20-25

### S3 Upload Fails

- Verify AWS credentials in `.env`
- Check bucket permissions (should allow PutObject)
- Ensure bucket exists in specified region

### Model Download Slow

- Models are cached in `data/huggingface_cache`
- First download: ~20-30GB for 14B models
- Subsequent runs: instant (cached)

## 📁 Project Structure

```
Sky/
├── skyreels_api.py         # Main FastAPI server
├── Dockerfile              # Container definition
├── docker-compose.yml      # Container orchestration
├── requirements.txt        # Python dependencies
├── env.example            # Environment template
├── README.md              # This file
├── API_EXAMPLES.md        # API usage examples
├── SkyReels-V2/           # SkyReels-V2 model code (auto-cloned)
└── data/                  # Persistent data (create this)
    ├── outputs/           # Temporary video storage
    └── huggingface_cache/ # Model cache
```

## 🔗 Links

- [SkyReels-V2 Official Repository](https://github.com/SkyworkAI/SkyReels-V2)
- [SkyReels-V2 Technical Report](https://arxiv.org/pdf/2504.13074)
- [SkyReels-V2 Models on HuggingFace](https://huggingface.co/collections/Skywork/skyreels-v2-6801b1b93df627d441d0d0d9)
- [SkyReels Playground](https://www.skyreels.ai)

## 📝 License

See `SkyReels-V2/LICENSE.txt` for SkyReels-V2 model license terms.

## 🤝 Acknowledgements


