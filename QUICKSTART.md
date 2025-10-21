# 🚀 Quick Start Guide

## Prerequisites
- AWS EC2 instance with GPU (g5.xlarge or better)
- NVIDIA Container Toolkit installed
- Docker & Docker Compose installed

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

## Step 2: Launch Service

```bash
chmod +x setup.sh
./setup.sh
```

## Step 3: Test API

### Generate Video
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "model_image": "Skywork/SkyReels-V2-I2V-14B-540P",
    "prompt": "A beautiful young woman touches her hair",
    "image_url": "https://i.postimg.cc/JnZkWXjM/asia-try.png"
  }'
```

**Response:**
```json
{"process_id": "abc-123-def"}
```

### Check Status
```bash
curl -X POST http://localhost:8000/status \
  -H "Content-Type: application/json" \
  -d '{"process_id": "abc-123-def"}'
```

**Response (Processing):**
```json
{
  "status": "processing",
  "message": "Starting video generation"
}
```

**Response (Done):**
```json
{
  "status": "done",
  "video_url": "https://your-bucket.s3.region.amazonaws.com/videos/user/process.mp4"
}
```

## Monitoring

View logs:
```bash
docker-compose logs -f
```

Check GPU usage:
```bash
docker exec -it video-generation-api nvidia-smi
```

## Troubleshooting

### GPU not detected
```bash
# Test NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### S3 upload fails
- Verify AWS credentials in `.env`
- Check bucket permissions (needs `s3:PutObject`)
- Ensure bucket exists in specified region

### Out of memory
Edit `task.sh` and reduce:
- `--num_frames 97` → `--num_frames 49`
- Or use smaller model

## Architecture

```
Client → API (POST /run) → Queue → Download Image → Generate Video → Upload S3 → Return URL
```

- **Queue**: Sequential processing (1 GPU)
- **Generation time**: ~2-5 minutes per video
- **GPU memory**: ~12-16GB required

