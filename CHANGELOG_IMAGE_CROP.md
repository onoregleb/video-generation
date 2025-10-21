# Changelog: Image Cropping Feature

## Summary

Added automatic image resizing and center-cropping to **960x544 pixels** for all input images.

## Changes Made

### 1. `SkyReels-V1/video_generate.py`
- ✅ Added `resize_and_crop_image()` function with center-crop algorithm
- ✅ Added PIL Image import
- ✅ Automatically process images when `task_type == "i2v"`
- ✅ Print original and resized dimensions for debugging

### 2. `task.sh`
- ✅ Fixed: Changed `--resolution 540P` to `--height 544 --width 960`
- ✅ Added `--task_type i2v` parameter
- ✅ Changed `--inference_steps` to `--num_inference_steps` (correct parameter name)
- ✅ Added `--video_num 1` to generate only one video instead of 2

### 3. `server_cloud.py`
- ✅ Removed `IMAGES_DIR` environment variable (no longer needed)
- ✅ Removed `download_image()` function (images now handled by diffusers)
- ✅ Pass image URL directly to task.sh (diffusers downloads automatically)
- ✅ Added automatic cleanup of local video files after S3 upload
- ✅ Removed unused imports: `requests`, `urllib.parse`, `pathlib`, `BackgroundTasks`, `List`

### 4. `docker-compose.yml`
- ✅ Removed `IMAGES_DIR` environment variable
- ✅ Removed `./data/input_images` volume mount

### 5. `Dockerfile`
- ✅ Removed `/mnt/tank/scratch/edubskiy/input_images` directory creation

### 6. `setup.sh`
- ✅ Removed `data/input_images` directory creation

### 7. Documentation
- ✅ Created `IMAGE_PROCESSING.md` - detailed documentation about image processing
- ✅ Created `test_image_crop.py` - test script for cropping functionality
- ✅ Updated `README.md` with image processing notes and workflow updates
- ✅ Updated environment variables table in README

## How It Works

### Before
```
User provides image URL
    ↓
Python downloads image to local disk
    ↓
Pass local path to video_generate.py
    ↓
Load image (any size)
    ✗ Size mismatch with model requirements
```

### After
```
User provides image URL
    ↓
Pass URL directly to video_generate.py
    ↓
diffusers.load_image() downloads from URL
    ↓
resize_and_crop_image() → 960x544
    ↓
Video generation with correct dimensions
    ✅ Perfect fit for model
```

## Benefits

1. ✅ **No manual image preparation** - users can send any image size
2. ✅ **No local storage** - images processed in memory
3. ✅ **Center crop strategy** - best framing preserved
4. ✅ **High quality resize** - LANCZOS resampling
5. ✅ **Automatic cleanup** - local videos deleted after S3 upload
6. ✅ **Simpler architecture** - fewer moving parts

## Technical Details

### Cropping Algorithm

```python
def resize_and_crop_image(image, target_width=960, target_height=544):
    # 1. Calculate aspect ratios
    target_aspect = 960 / 544 = 1.765
    
    # 2. Resize to cover target (one dimension will be larger)
    if image is wider:
        resize based on height → crop width
    else:
        resize based on width → crop height
    
    # 3. Center crop to exact dimensions
    crop from center → 960x544
```

### Image Quality

- **Resampling**: `Image.Resampling.LANCZOS` (high quality)
- **No distortion**: Aspect ratio preserved during resize
- **Center focus**: Important content typically in center

## Testing

Run the test script:
```bash
python3 test_image_crop.py
```

Expected output:
```
✅ Full HD landscape     1920x1080 →  960x544
✅ Full HD portrait      1080x1920 →  960x544
✅ Square                1000x1000 →  960x544
✅ Wide panorama         3000x2000 →  960x544
✅ Small landscape        800x600  →  960x544
✅ Small portrait         600x800  →  960x544
All tests passed! ✅
```

## Migration Notes

### For Users
- No changes required! Just send any image URL
- Images are automatically processed

### For Developers
- `IMAGES_DIR` is no longer used
- Images are not stored locally (memory only)
- task.sh now uses correct parameters for video_generate.py
- Only 1 video generated per request (not 2)

## API Example

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "model_image": "Skywork/SkyReels-V2-I2V-14B-540P",
    "prompt": "A person walking",
    "image_url": "https://example.com/any-size-image.jpg"
  }'
```

Image will be automatically:
1. Downloaded from URL
2. Resized and cropped to 960x544
3. Processed by video generation model

## Files Modified

- ✅ `SkyReels-V1/video_generate.py` - Added cropping logic
- ✅ `task.sh` - Fixed parameters
- ✅ `server_cloud.py` - Removed image download, added cleanup
- ✅ `docker-compose.yml` - Removed IMAGES_DIR
- ✅ `Dockerfile` - Removed input_images directory
- ✅ `setup.sh` - Removed input_images directory
- ✅ `README.md` - Updated documentation

## New Files

- ✅ `IMAGE_PROCESSING.md` - Detailed image processing documentation
- ✅ `test_image_crop.py` - Test script for cropping
- ✅ `CHANGELOG_IMAGE_CROP.md` - This file

