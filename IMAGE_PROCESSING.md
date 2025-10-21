# Image Processing and Cropping

## Overview

The system automatically resizes and crops input images to **960x544** pixels (the required resolution for the SkyReels video generation model).

## How It Works

### 1. Automatic Resize and Center Crop

When you provide an image URL in the API request, the system:

1. **Downloads** the image (if URL provided) or loads local file
2. **Resizes** the image to cover the target dimensions while maintaining aspect ratio
3. **Center crops** the image to exactly 960x544 pixels
4. **Processes** the cropped image through the video generation model

### 2. Cropping Strategy

The cropping algorithm uses a **center crop** strategy:

- If the image is **wider** than the target aspect ratio (1.76):
  - Resize based on height (544px)
  - Crop excess width from left and right sides equally
  
- If the image is **taller** than the target aspect ratio:
  - Resize based on width (960px)
  - Crop excess height from top and bottom equally

### 3. Examples

| Original Size | Action | Result |
|---------------|--------|--------|
| 1920x1080 (16:9) | Resize to 963x542 → Crop to 960x544 | ✅ 960x544 |
| 1080x1920 (9:16) | Resize to 306x544 → Expand & Crop | ✅ 960x544 |
| 1000x1000 (1:1) | Resize to 960x960 → Crop to 960x544 | ✅ 960x544 |
| 3000x2000 (3:2) | Resize to 816x544 → Expand & Crop | ✅ 960x544 |

## API Usage

Simply provide an image URL in your request - no need to pre-process:

```json
{
  "user_id": "user123",
  "model_image": "Skywork/SkyReels-V2-I2V-14B-540P",
  "prompt": "A person walking in the park",
  "image_url": "https://example.com/photo.jpg"
}
```

The system handles all image processing automatically!

## Testing

Run the test script to verify cropping behavior:

```bash
python3 test_image_crop.py
```

Expected output:
```
Target dimensions: 960x544
Target aspect ratio: 1.765
======================================================================
✅ Full HD landscape     1920x1080 →  960x544
✅ Full HD portrait      1080x1920 →  960x544
✅ Square                1000x1000 →  960x544
✅ Wide panorama         3000x2000 →  960x544
✅ Small landscape        800x600  →  960x544
✅ Small portrait         600x800  →  960x544
======================================================================
All tests passed! ✅
```

## Technical Details

### Implementation

Located in: `SkyReels-V1/video_generate.py`

```python
def resize_and_crop_image(image, target_width=960, target_height=544):
    """
    Resize and crop image to target dimensions while maintaining aspect ratio.
    Uses center crop strategy.
    """
    # ... implementation ...
```

### Image Quality

- **Resampling method**: LANCZOS (high quality)
- **Aspect ratio**: Preserved during resize, then center-cropped
- **No distortion**: Images are never stretched or squashed

## Supported Image Formats

All formats supported by PIL/Pillow:
- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)
- GIF (.gif)
- BMP (.bmp)
- TIFF (.tiff)

## Notes

- Images can be provided as **URLs** (downloaded automatically) or **local paths**
- No need to manually resize images before uploading
- The cropping is **non-destructive** - original images are not modified
- Processing happens in memory - no temporary files created

