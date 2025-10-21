import argparse
import os
import time
import random
from PIL import Image

from diffusers.utils import export_to_video
from diffusers.utils import load_image

from skyreelsinfer import TaskType
from skyreelsinfer.offload import OffloadConfig
from skyreelsinfer.skyreels_video_infer import SkyReelsVideoInfer


def resize_and_crop_image(image, target_width=960, target_height=544):
    """
    Resize and crop image to target dimensions while maintaining aspect ratio.
    Uses center crop strategy.
    
    Args:
        image: PIL Image object
        target_width: Target width (default 960)
        target_height: Target height (default 544)
    
    Returns:
        PIL Image object resized and cropped to target dimensions
    """
    if not isinstance(image, Image.Image):
        raise ValueError("Input must be a PIL Image object")
    
    # Get original dimensions
    orig_width, orig_height = image.size
    
    # Calculate aspect ratios
    target_aspect = target_width / target_height
    orig_aspect = orig_width / orig_height
    
    # Resize image to fill the target dimensions (one dimension will be larger)
    if orig_aspect > target_aspect:
        # Original is wider - resize based on height
        new_height = target_height
        new_width = int(orig_width * (target_height / orig_height))
    else:
        # Original is taller - resize based on width
        new_width = target_width
        new_height = int(orig_height * (target_width / orig_width))
    
    # Resize image
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Calculate crop coordinates (center crop)
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height
    
    # Crop to target dimensions
    image = image.crop((left, top, right, bottom))
    
    return image

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_id", type=str, default="Skywork/SkyReels-V1-Hunyuan-T2V")
    parser.add_argument("--outdir", type=str, default="skyreels")
    parser.add_argument("--guidance_scale", type=float, default=6.0)
    parser.add_argument("--num_frames", type=int, default=97)
    parser.add_argument("--num_inference_steps", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--prompt", type=str, default="FPS-24, A 3D model of a 1800s victorian house.")
    parser.add_argument(
        "--negative_prompt",
        type=str,
        default="Aerial view, aerial view, overexposed, low quality, deformation, a poor composition, bad hands, bad teeth, bad eyes, bad limbs, distortion",
    )
    parser.add_argument("--height", type=int, default=544)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--gpu_num", type=int, default=1)
    parser.add_argument("--video_num", type=int, default=2)
    parser.add_argument("--task_type", type=str, default="t2v", choices=["t2v", "i2v"])
    parser.add_argument("--image", type=str, default="")
    parser.add_argument("--embedded_guidance_scale", type=float, default=1.0)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--quant", action="store_true")
    parser.add_argument("--offload", action="store_true")
    parser.add_argument("--high_cpu_memory", action="store_true")
    parser.add_argument("--parameters_level", action="store_true")
    parser.add_argument("--compiler_transformer", action="store_true")
    parser.add_argument("--sequence_batch", action="store_true")
    parser.add_argument("--mbps", type=float, default=7)

    args = parser.parse_args()

    out_dir = f"results/{args.outdir}"
    os.makedirs(out_dir, exist_ok=True)

    if args.task_type == "i2v":
        image = load_image(args.image)
        # Resize and crop image to target dimensions
        print(f"Original image size: {image.size}")
        image = resize_and_crop_image(image, target_width=args.width, target_height=args.height)
        print(f"Resized and cropped image to: {image.size}")

    if args.seed == -1:
        random.seed(time.time())
        args.seed = int(random.randrange(4294967294))

    predictor = SkyReelsVideoInfer(
        task_type=TaskType.I2V if args.task_type == "i2v" else TaskType.T2V,
        model_id=args.model_id,
        quant_model=args.quant,
        world_size=args.gpu_num,
        is_offload=args.offload,
        offload_config=OffloadConfig(
            high_cpu_memory=args.high_cpu_memory,
            parameters_level=args.parameters_level,
            compiler_transformer=args.compiler_transformer,
        ),
        enable_cfg_parallel=args.guidance_scale > 1.0,
    )
    print("finish pipeline init")
    kwargs = {
        "prompt": args.prompt,
        "height": args.height,
        "width": args.width,
        "num_frames": args.num_frames,
        "num_inference_steps": args.num_inference_steps,
        "seed": args.seed,
        "guidance_scale": args.guidance_scale,
        "embedded_guidance_scale": args.embedded_guidance_scale,
        "negative_prompt": args.negative_prompt,
        "cfg_for": args.sequence_batch,
    }
    if args.task_type == "i2v":
        kwargs["image"] = image

    # 20250223 pftq: customizable bitrate
    # Function to check if FFmpeg is installed
    import subprocess  # For FFmpeg functionality
    import numpy as np  # For frame conversion
    import cv2  # For OpenCV fallback


    def is_ffmpeg_installed():
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


    # FFmpeg-based video saving with bitrate control
    def save_video_with_ffmpeg(frames, output_path, fps, bitrate_mbps):
        frames = [np.array(frame).astype(np.uint8) for frame in frames]  # Преобразуем кадры в uint8
        height, width, _ = frames[0].shape
        bitrate = f"{bitrate_mbps}M"
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{width}x{height}",
            "-pix_fmt", "rgb24",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-b:v", bitrate,
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            output_path
        ]
        try:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            for frame in frames:
                process.stdin.write(frame.tobytes())
            process.stdin.close()
            process.wait()
            if process.returncode != 0:
                stderr_output = process.stderr.read().decode()
                print(f"FFmpeg error: {stderr_output}")
            else:
                print(f"Video saved to {output_path} with FFmpeg")
        except BrokenPipeError as e:
            print("FFmpeg process terminated prematurely:", e)
            print("FFmpeg stderr:", process.stderr.read().decode())


    # Fallback OpenCV-based video saving
    def save_video_with_opencv(frames, output_path, fps, bitrate_mbps):
        frames = [np.array(frame) for frame in frames]
        height, width, _ = frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        # Note: cv2.CAP_PROP_BITRATE is not supported, so bitrate_mbps is ignored
        for frame in frames:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR for OpenCV
            writer.write(frame)
        writer.release()
        print(f"Video saved to {output_path} with OpenCV (bitrate control unavailable)")


    # Wrapper to choose between FFmpeg and OpenCV
    def save_video_with_quality(frames, output_path, fps, bitrate_mbps):
        if is_ffmpeg_installed():
            save_video_with_ffmpeg(frames, output_path, fps, bitrate_mbps)
        else:
            print("FFmpeg not found. Falling back to OpenCV (bitrate not customizable).")
            save_video_with_opencv(frames, output_path, fps, bitrate_mbps)


    for idx in range(args.video_num):
        output = predictor.inference(kwargs)
        # video_out_file = f"{args.prompt[:100].replace('/','')}_{args.seed}_{idx}.mp4"
        # export_to_video(output, f"{out_dir}/{video_out_file}", fps=args.fps)

        # 20250223 pftq: More useful filename and higher customizable bitrate
        from datetime import datetime

        now = datetime.now()
        formatted_time = now.strftime('%Y-%m-%d_%H-%M-%S')
        video_out_file = formatted_time + f"_cfg-{args.guidance_scale}_steps-{args.num_inference_steps}_{args.prompt[:20].replace('/', '')}_seed-{args.seed}_{idx}.mp4"
        save_video_with_quality(output, f"{out_dir}/{video_out_file}", args.fps, args.mbps)