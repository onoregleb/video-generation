"""
FastAPI server for SkyReels-V2 Image-to-Video generation
Simplified API with support for 540P and 720P resolutions
"""
import os
import gc
import json
import uuid
import time
import random
import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
import threading
import queue
import sys

import imageio
import torch
from diffusers.utils import load_image

# Add SkyReels-V2 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'SkyReels-V2'))

from skyreels_v2_infer.modules import download_model
from skyreels_v2_infer.pipelines import Image2VideoPipeline
from skyreels_v2_infer.pipelines import resizecrop

# Configuration
OUTPUT_BASE_DIR = os.environ.get("OUTPUT_BASE_DIR", "/app/data/outputs")
HF_HOME = os.environ.get("HF_HOME", "/app/data/huggingface_cache")
TRANSFORMERS_CACHE = os.environ.get("TRANSFORMERS_CACHE", HF_HOME)

# S3 Configuration
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "storage.modera.fashion")
S3_REGION = os.environ.get("S3_REGION", "eu-central-2")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "")
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", None)

# Create necessary directories
os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
os.makedirs(HF_HOME, exist_ok=True)

# Set HuggingFace cache
os.environ["HF_HOME"] = HF_HOME
os.environ["TRANSFORMERS_CACHE"] = TRANSFORMERS_CACHE

# In-memory storage for process status
process_status = {}

# Task queue
job_queue = queue.Queue()
stop_worker = False

# FastAPI app
app = FastAPI(title="SkyReels-V2 Image-to-Video API")

# Default prompt for image-to-video
DEFAULT_PROMPT = "A cinematic video with smooth motion and natural movement"

# Model mapping for different resolutions
RESOLUTION_MODELS = {
    "540P": "Skywork/SkyReels-V2-I2V-14B-540P",
    "720P": "Skywork/SkyReels-V2-I2V-14B-720P"
}


class Image2VideoRequest(BaseModel):
    user_id: str
    image_url: HttpUrl
    resolution: str = "540P"  # 540P or 720P
    prompt: Optional[str] = None  # Optional prompt, uses default if not provided
    num_frames: int = 97
    guidance_scale: float = 5.0
    shift: float = 5.0
    inference_steps: int = 30
    fps: int = 24
    seed: Optional[int] = None
    use_teacache: bool = True
    teacache_thresh: float = 0.3
    use_ret_steps: bool = True
    offload: bool = True
    process_id: Optional[str] = None


class StatusRequest(BaseModel):
    process_id: str


def get_s3_client():
    """Create and return an S3 client"""
    if not S3_ACCESS_KEY or not S3_SECRET_KEY:
        raise Exception("S3 credentials not configured")
    
    session = boto3.session.Session()
    s3_client = session.client(
        service_name='s3',
        region_name=S3_REGION,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        endpoint_url=S3_ENDPOINT_URL
    )
    return s3_client


def upload_to_s3(local_file_path: str, process_id: str, user_id: str) -> str:
    """Upload a file to S3 bucket"""
    try:
        s3_client = get_s3_client()
        s3_key = f"videos/{user_id}/{process_id}.mp4"
        
        s3_client.upload_file(
            Filename=local_file_path,
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            ExtraArgs={'ContentType': 'video/mp4'}
        )
        
        if S3_ENDPOINT_URL:
            video_url = f"{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{s3_key}"
        else:
            video_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        
        return video_url
    except ClientError as e:
        raise Exception(f"Failed to upload to S3: {str(e)}")
    except Exception as e:
        raise Exception(f"Error during S3 upload: {str(e)}")


def generate_video(
    process_id: str,
    user_id: str,
    image_url: str,
    resolution: str = "540P",
    prompt: Optional[str] = None,
    num_frames: int = 97,
    guidance_scale: float = 5.0,
    shift: float = 5.0,
    inference_steps: int = 30,
    fps: int = 24,
    seed: Optional[int] = None,
    use_teacache: bool = True,
    teacache_thresh: float = 0.3,
    use_ret_steps: bool = True,
    offload: bool = True
):
    """Generate video from image using SkyReels-V2"""
    try:
        start_time = time.time()
        process_status[process_id] = {
            "status": "processing",
            "start_time": start_time,
            "user_id": user_id,
            "message": "Initializing..."
        }
        
        # Use default prompt if not provided
        if prompt is None or prompt.strip() == "":
            prompt = DEFAULT_PROMPT
        
        # Validate resolution
        if resolution not in RESOLUTION_MODELS:
            raise ValueError(f"Invalid resolution: {resolution}. Must be one of: {list(RESOLUTION_MODELS.keys())}")
        
        model_id = RESOLUTION_MODELS[resolution]
        
        print(f"\n{'='*60}")
        print(f"Starting Image-to-Video generation")
        print(f"{'='*60}")
        print(f"Process ID: {process_id}")
        print(f"User ID: {user_id}")
        print(f"Model: {model_id}")
        print(f"Resolution: {resolution}")
        print(f"Prompt: {prompt}")
        print(f"Image URL: {image_url}")
        print(f"{'='*60}\n")
        
        # Set seed
        if seed is None:
            random.seed(time.time())
            seed = int(random.randrange(4294967294))
        print(f"Using seed: {seed}")
        
        # Download model if needed
        print("Checking model...")
        model_id = download_model(model_id)
        print(f"Model ready: {model_id}")
        
        # Set resolution dimensions
        if resolution == "540P":
            height, width = 544, 960
        elif resolution == "720P":
            height, width = 720, 1280
        
        # Load image
        print(f"Loading image from: {image_url}")
        process_status[process_id]["message"] = "Loading image..."
        image = load_image(image_url).convert("RGB")
        image_width, image_height = image.size
        print(f"Original image size: {image_width}x{image_height}")
        
        # Negative prompt
        negative_prompt = (
            "Bright tones, overexposed, static, blurred details, subtitles, style, works, "
            "paintings, images, static, overall gray, worst quality, low quality, "
            "JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, "
            "poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, "
            "still picture, messy background, three legs, many people in the background, walking backwards"
        )
        
        # Initialize Image-to-Video pipeline
        print("Initializing Image-to-Video pipeline...")
        process_status[process_id]["message"] = "Initializing pipeline..."
        
        pipe = Image2VideoPipeline(
            model_path=model_id,
            dit_path=model_id,
            use_usp=False,
            offload=offload
        )
        
        # Resize and crop image based on resolution
        # Swap dimensions if image is portrait
        if image_height > image_width:
            height, width = width, height
        
        image = resizecrop(image, height, width)
        print(f"Resized and cropped image to: {width}x{height}")
        
        print("Pipeline initialized successfully")
        
        # Enable teacache if requested
        if use_teacache:
            print("Enabling teacache for faster inference...")
            process_status[process_id]["message"] = "Enabling teacache..."
            pipe.transformer.initialize_teacache(
                enable_teacache=True,
                num_steps=inference_steps,
                teacache_thresh=teacache_thresh,
                use_ret_steps=use_ret_steps,
                ckpt_dir=model_id
            )
        
        # Prepare generation kwargs
        kwargs = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "image": image,
            "num_frames": num_frames,
            "num_inference_steps": inference_steps,
            "guidance_scale": guidance_scale,
            "shift": shift,
            "generator": torch.Generator(device="cuda").manual_seed(seed),
            "height": height,
            "width": width,
        }
        
        # Generate video
        print("\nStarting video generation...")
        print(f"Parameters: {json.dumps({k: str(v) if not isinstance(v, (int, float, str, bool)) else v for k, v in kwargs.items()}, indent=2)}")
        process_status[process_id]["message"] = "Generating video..."
        
        generation_start = time.time()
        
        # Set CUDA memory config
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
        
        with torch.cuda.amp.autocast(dtype=pipe.transformer.dtype), torch.no_grad():
            video_frames = pipe(**kwargs)[0]
        
        generation_time = time.time() - generation_start
        print(f"\n✅ Video generation completed in {generation_time:.2f} seconds ({generation_time/60:.2f} minutes)")
        
        # Save video
        output_dir = os.path.join(OUTPUT_BASE_DIR, user_id, process_id)
        os.makedirs(output_dir, exist_ok=True)
        
        current_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        safe_prompt = prompt[:30].replace('/', '_').replace('\\', '_').replace(':', '_')
        video_filename = f"{safe_prompt}_{seed}_{current_time}.mp4"
        video_path = os.path.join(output_dir, video_filename)
        
        print(f"Saving video to: {video_path}")
        process_status[process_id]["message"] = "Saving video..."
        
        imageio.mimwrite(
            video_path,
            video_frames,
            fps=fps,
            quality=8,
            output_params=["-loglevel", "error"]
        )
        print(f"✅ Video saved successfully")
        
        # Upload to S3
        print("Uploading to S3...")
        process_status[process_id]["message"] = "Uploading to S3..."
        s3_url = upload_to_s3(video_path, process_id, user_id)
        print(f"✅ Uploaded to S3: {s3_url}")
        
        # Clean up local file
        try:
            os.remove(video_path)
            print(f"Cleaned up local file: {video_path}")
        except Exception as e:
            print(f"Warning: Failed to delete local file: {e}")
        
        # Clean up GPU memory
        del pipe
        gc.collect()
        torch.cuda.empty_cache()
        
        # Update status
        total_time = time.time() - start_time
        process_status[process_id].update({
            "status": "done",
            "video_url": s3_url,
            "generation_time_seconds": round(total_time, 2),
            "message": "Video generation completed"
        })
        
        print(f"\n{'='*60}")
        print(f"✅ Process completed successfully")
        print(f"Total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        print(f"Video URL: {s3_url}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        end_time = time.time()
        start_time_val = process_status.get(process_id, {}).get("start_time", end_time)
        total_time = end_time - start_time_val
        
        error_msg = str(e)
        print(f"\n❌ Error in video generation after {total_time:.2f} seconds: {error_msg}")
        
        process_status[process_id] = {
            "status": "failed",
            "error": error_msg,
            "generation_time_seconds": round(total_time, 2),
            "user_id": user_id
        }
        
        # Clean up GPU memory on error
        gc.collect()
        torch.cuda.empty_cache()


def queue_worker():
    """Background worker to process video generation jobs"""
    while not stop_worker:
        try:
            job = job_queue.get(timeout=1)
        except queue.Empty:
            continue
        
        try:
            generate_video(**job)
        except Exception as e:
            process_id = job.get('process_id', 'unknown')
            print(f"❌ Fatal error in queue worker for process {process_id}: {str(e)}")
            process_status[process_id] = {
                'status': 'failed',
                'error': f"Fatal error: {str(e)}",
                'user_id': job.get('user_id', 'unknown')
            }
        finally:
            job_queue.task_done()


# Start worker thread
worker_thread = threading.Thread(target=queue_worker, daemon=True)
worker_thread.start()


@app.post("/generate")
async def generate(req: Image2VideoRequest):
    """Submit an image-to-video generation job"""
    process_id = req.process_id if req.process_id else str(uuid.uuid4())
    
    process_status[process_id] = {
        "status": "queued",
        "created_at": time.time(),
        "user_id": req.user_id
    }
    
    job = {
        'process_id': process_id,
        'user_id': req.user_id,
        'image_url': str(req.image_url),
        'resolution': req.resolution,
        'prompt': req.prompt,
        'num_frames': req.num_frames,
        'guidance_scale': req.guidance_scale,
        'shift': req.shift,
        'inference_steps': req.inference_steps,
        'fps': req.fps,
        'seed': req.seed,
        'use_teacache': req.use_teacache,
        'teacache_thresh': req.teacache_thresh,
        'use_ret_steps': req.use_ret_steps,
        'offload': req.offload
    }
    
    job_queue.put(job)
    
    print(f"\n📝 Image-to-Video job queued: {process_id}")
    print(f"User: {req.user_id}")
    print(f"Resolution: {req.resolution}")
    print(f"Image URL: {req.image_url}")
    print(f"Prompt: {req.prompt or DEFAULT_PROMPT}")
    print(f"Queue size: {job_queue.qsize()}\n")
    
    return {"process_id": process_id}


@app.post("/status")
def get_status(req: StatusRequest):
    """Get the status of a video generation job"""
    if req.process_id not in process_status:
        raise HTTPException(status_code=404, detail="Process not found")
    
    full_status = process_status[req.process_id]
    
    response = {
        "status": full_status.get("status"),
        "user_id": full_status.get("user_id")
    }
    
    if "video_url" in full_status:
        response["video_url"] = full_status["video_url"]
    
    if "generation_time_seconds" in full_status:
        response["generation_time_seconds"] = full_status["generation_time_seconds"]
    
    if full_status.get("status") == "failed" and "error" in full_status:
        response["error"] = full_status["error"]
    
    if "message" in full_status:
        response["message"] = full_status["message"]
    
    return response


@app.get("/processes")
def list_processes():
    """List all processes (for debugging)"""
    return process_status


@app.get("/")
def root():
    """API root endpoint"""
    return {
        "name": "SkyReels-V2 Image-to-Video API",
        "version": "2.0",
        "description": "Convert images to videos with 540P or 720P resolution",
        "status": "running",
        "supported_resolutions": list(RESOLUTION_MODELS.keys()),
        "default_prompt": DEFAULT_PROMPT,
        "queue_size": job_queue.qsize()
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "cuda_available": torch.cuda.is_available(),
        "cuda_devices": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "queue_size": job_queue.qsize()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
