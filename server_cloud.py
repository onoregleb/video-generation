import os
import json
import uuid
import time
import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Dict, Optional, Union
import threading
import queue
import subprocess

# Пути для хранения и доступа к видео
OUTPUT_BASE_DIR = os.environ.get("OUTPUT_BASE_DIR", "")
SCRIPT_PATH = os.environ.get("SCRIPT_PATH", "")

# S3 конфигурация
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "storage.modera.fashion")
S3_REGION = os.environ.get("S3_REGION", "eu-central-2")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "")
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", None)

# In-memory storage for process status (in production, use a proper database)
process_status = {}

# Очередь задач и воркер
job_queue = queue.Queue()
queue_lock = threading.Lock()

# Флаг для остановки воркера (если потребуется)
stop_worker = False

app = FastAPI()

class RunRequest(BaseModel):
    user_id: str
    model_image: str
    prompt: str = None
    image_url: Union[HttpUrl, str] = None  # URL изображения для скачивания
    process_id: Optional[str] = None  # Optional custom process_id

class StatusRequest(BaseModel):
    process_id: str

class VideoGenerationResult(BaseModel):
    status: str
    # progress поле удалено
    video_url: Optional[str] = None
    error: Optional[str] = None
    slurm_job_id: Optional[str] = None

def get_s3_client():
    """Create and return an S3 client"""
    if not S3_ACCESS_KEY or not S3_SECRET_KEY:
        raise Exception("S3 credentials not configured. Set S3_ACCESS_KEY and S3_SECRET_KEY environment variables.")
    
    session = boto3.session.Session()
    s3_client = session.client(
        service_name='s3',
        region_name=S3_REGION,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        endpoint_url=S3_ENDPOINT_URL
    )
    return s3_client

def upload_to_s3(local_file_path: str, process_id: str, user_id: str):
    """Upload a file to S3 bucket"""
    try:
        s3_client = get_s3_client()
        
        # Создаем ключ для объекта в S3 (путь к файлу)
        s3_key = f"videos/{user_id}/{process_id}.mp4"
        
        # Загружаем файл в S3
        s3_client.upload_file(
            Filename=local_file_path,
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            ExtraArgs={'ContentType': 'video/mp4'}
        )
        
        # Генерируем URL для доступа к файлу
        if S3_ENDPOINT_URL:
            # Для совместимых с S3 хранилищ (например, MinIO)
            video_url = f"{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{s3_key}"
        else:
            # Для AWS S3
            video_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        
        return video_url
    except ClientError as e:
        raise Exception(f"Failed to upload to S3: {str(e)}")
    except Exception as e:
        raise Exception(f"Error during S3 upload: {str(e)}")




def run_video_generation(process_id: str, user_id: str, model_image: str, prompt: str = None, image_url: str = None):
    """Run video generation directly using subprocess"""
    try:
        # Update status to "processing"
        process_status[process_id] = {
            "status": "processing",
            "start_time": time.time(),
            "user_id": user_id
        }
        
        # Prepare environment variables for task.sh
        env = os.environ.copy()
        env["PROCESS_ID"] = process_id
        env["USER_ID"] = user_id
        env["MODEL_IMAGE"] = model_image
        if prompt:
            env["PROMPT"] = prompt
        # Pass image URL directly - diffusers' load_image() supports URLs
        if image_url:
            env["IMAGE_PATH"] = image_url
        
        process_status[process_id].update({
            "status": "processing",
            "message": "Starting video generation"
        })
        
        # Run task.sh directly
        print(f"Starting video generation for process {process_id}")
        result = subprocess.run(
            [SCRIPT_PATH],
            env=env,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else "Unknown error during video generation"
            print(f"Video generation failed: {error_msg}")
            process_status[process_id].update({
                "status": "failed",
                "error": error_msg
            })
            return
        
        # Check status file for results
        output_dir = f"{OUTPUT_BASE_DIR}/{user_id}/{process_id}"
        status_file_path = f"{output_dir}/status.json"
        
        if os.path.exists(status_file_path):
            with open(status_file_path, 'r') as f:
                status_data = json.loads(f.read())
            
            if status_data.get("status") == "done":
                local_video_path = status_data.get("video_url", "")
                
                if local_video_path and os.path.exists(local_video_path):
                    # Upload to S3
                    process_status[process_id].update({
                        "status": "processing",
                        "message": "Uploading video to S3"
                    })
                    
                    s3_url = upload_to_s3(local_video_path, process_id, user_id)
                    
                    # Clean up local video file after successful S3 upload
                    try:
                        os.remove(local_video_path)
                        print(f"Cleaned up local video file: {local_video_path}")
                    except Exception as e:
                        print(f"Warning: Failed to delete local video file: {e}")
                    
                    process_status[process_id].update({
                        "status": "done",
                        "video_url": s3_url,
                        "message": "Video uploaded to S3"
                    })
                    print(f"Video generation completed successfully: {s3_url}")
                else:
                    process_status[process_id].update({
                        "status": "failed",
                        "error": "Video file not found after generation"
                    })
            else:
                process_status[process_id].update({
                    "status": "failed",
                    "error": status_data.get("error", "Unknown error")
                })
        else:
            process_status[process_id].update({
                "status": "failed",
                "error": "Status file not found after video generation"
            })
            
    except subprocess.TimeoutExpired:
        process_status[process_id] = {
            "status": "failed",
            "error": "Video generation timed out (exceeded 1 hour)"
        }
    except Exception as e:
        print(f"Exception in run_video_generation: {str(e)}")
        process_status[process_id] = {
            "status": "failed",
            "error": str(e)
        }
# Очередь задач и воркер
job_queue = queue.Queue()
queue_lock = threading.Lock()

# Флаг для остановки воркера (если потребуется)
stop_worker = False

def queue_worker():
    while not stop_worker:
        try:
            job = job_queue.get(timeout=1)
        except queue.Empty:
            continue
        try:
            run_video_generation(**job)
        except Exception as e:
            process_id = job.get('process_id', 'unknown')
            process_status[process_id] = {
                'status': 'failed',
                'error': str(e)
            }
        finally:
            job_queue.task_done()

# Запуск воркера при старте приложения
worker_thread = threading.Thread(target=queue_worker, daemon=True)
worker_thread.start()

@app.post("/run")
async def run(req: RunRequest):
    process_id = req.process_id if req.process_id else str(uuid.uuid4())
    process_status[process_id] = {
        "status": "queued",
        "created_at": time.time(),
        "user_id": req.user_id
    }
    # Кладём задачу в очередь
    job = {
        'process_id': process_id,
        'user_id': req.user_id,
        'model_image': req.model_image,
        'prompt': req.prompt,
        'image_url': req.image_url
    }
    job_queue.put(job)
    return {"process_id": process_id}

@app.post("/status")
def get_status(req: StatusRequest):
    # Check if process exists
    if req.process_id not in process_status:
        raise HTTPException(status_code=404, detail="Process not found")
    
    # Return current status
    return process_status[req.process_id]

@app.get("/processes")
def list_processes():
    """List all processes (for debugging)"""
    return process_status

