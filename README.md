# Video Generation Service

This repository contains a Docker-based video generation service for creating videos using SkyReels models on AWS EC2 instances with GPU support.

## Prerequisites

- Docker & Docker Compose
- NVIDIA Container Toolkit (for GPU support)
- AWS EC2 instance with GPU (recommended: g5.xlarge or higher)
- AWS S3 bucket for video storage

## Architecture

1. **FastAPI Server** - REST API for accepting video generation requests
2. **Task Queue** - Sequential processing of video generation jobs (single GPU)
3. **SkyReels-V1** - Video generation engine using Diffusers
4. **AWS S3** - Storage for generated videos

## File Structure

- `Dockerfile` - Container definition
- `docker-compose.yml` - Container orchestration
- `.env` - Environment variables (create from template)
- `server_cloud.py` - Main API server
- `task.sh` - Video generation bash script
- `setup.sh` - Setup and launch helper script
- `requirements.txt` - Python dependencies
- `SkyReels-V1/` - Video generation model code

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Configure environment variables

Create a `.env` file with your AWS credentials:

```bash
# AWS S3 Configuration
S3_BUCKET_NAME=your-bucket-name
S3_REGION=eu-central-2
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key

# GPU Configuration (default: 0)
CUDA_VISIBLE_DEVICES=0
```

### 3. Run the setup script

```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Create necessary directories (`data/outputs`, `data/huggingface_cache`, `data/models`)
- Verify Docker installation
- Start the Docker container with GPU support

### 4. Manual Setup (Alternative)

```bash
# Create required directories
mkdir -p data/outputs data/huggingface_cache data/models

# Start the container
docker-compose up -d --build
```

## API Usage

The API will be available at `http://localhost:8000/`.

### Generate Video

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "model_image": "Skywork/SkyReels-V2-I2V-14B-540P",
    "prompt": "A beautiful young woman touches her hair",
    "image_url": "https://example.com/image.jpg"
  }'
```

**Response:**
```json
{
  "process_id": "uuid-generated-process-id"
}
```

**Note:** Images are automatically resized and center-cropped to **960x544** pixels. You can provide images in any size or aspect ratio. See [IMAGE_PROCESSING.md](IMAGE_PROCESSING.md) for details.

### Check Status

```bash
curl -X POST http://localhost:8000/status \
  -H "Content-Type: application/json" \
  -d '{"process_id": "your-process-id"}'
```

**Response (Processing):**
```json
{
  "status": "processing",
  "user_id": "test_user"
}
```

**Response (Completed):**
```json
{
  "status": "done",
  "user_id": "test_user",
  "video_url": "https://your-bucket.s3.region.amazonaws.com/videos/user_id/process_id.mp4",
  "generation_time_seconds": 222.22
}
```

**Response (Failed):**
```json
{
  "status": "failed",
  "user_id": "test_user",
  "error": "Error message description",
  "generation_time_seconds": 54.33
}
```

**Time Tracking:**
- `generation_time_seconds`: Total time taken for video generation in seconds (also logged to console)

### List All Processes (Debug)

```bash
curl http://localhost:8000/processes
```

## Container Management

### View logs
```bash
docker-compose logs -f
```

### Stop container
```bash
docker-compose down
```

### Restart container
```bash
docker-compose restart
```

### Rebuild container
```bash
docker-compose up -d --build
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `S3_BUCKET_NAME` | `storage.modera.fashion` | AWS S3 bucket name |
| `S3_REGION` | `eu-central-2` | AWS S3 region |
| `S3_ACCESS_KEY` | - | AWS Access Key (required) |
| `S3_SECRET_KEY` | - | AWS Secret Key (required) |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU device ID |
| `OUTPUT_BASE_DIR` | `/mnt/tank/scratch/edubskiy/outputs` | Output directory (temporary) |
| `SCRIPT_PATH` | `/app/task.sh` | Path to generation script |

### Model Configuration

The service uses HuggingFace models that are automatically downloaded on first use:
- Default model: `Skywork/SkyReels-V2-I2V-14B-540P`
- Models are cached in `data/huggingface_cache`

## Workflow

1. **Request** - Client sends POST to `/run` with image URL and prompt
2. **Queue** - Request added to processing queue (sequential processing)
3. **Process Image** - Image loaded from URL and automatically resized/cropped to 960x544
4. **Generate** - Video generated using SkyReels-V1 model
5. **Upload** - Video uploaded to AWS S3
6. **Cleanup** - Local video file deleted after successful S3 upload
7. **Response** - S3 URL returned to client

## Troubleshooting

### CUDA/GPU issues
```bash
# Check if GPU is accessible in container
docker exec -it video-generation-api nvidia-smi
```

### Out of memory
- Reduce `num_frames` in `task.sh` (default: 97)
- Enable `--offload` flag (already enabled by default)
- Use smaller resolution (currently: 540P)

### S3 upload fails
- Verify AWS credentials in `.env`
- Check S3 bucket permissions
- Ensure bucket exists in specified region

### Video generation fails
- Check logs: `docker-compose logs -f`
- Verify PyTorch and CUDA are properly installed
- Check disk space in `data/` directories

## Performance

- **First run**: ~10-15 minutes (model download)
- **Subsequent runs**: ~2-5 minutes per video (depending on GPU)
- **Memory**: Requires ~48-60GB GPU RAM
- **Recommended GPU**: NVIDIA H100, T4, or better

## License

See `SkyReels-V1/LICENSE.txt` for SkyReels model license. 