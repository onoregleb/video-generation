#!/usr/bin/env python3
"""
Test script for image cropping/resizing functionality
"""
from PIL import Image
import sys
import os

# Add SkyReels-V1 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'SkyReels-V1'))

from video_generate import resize_and_crop_image


def test_resize_and_crop():
    """Test the resize and crop function with various image sizes"""
    
    test_cases = [
        # (width, height, description)
        (1920, 1080, "Full HD landscape"),
        (1080, 1920, "Full HD portrait"),
        (1000, 1000, "Square"),
        (3000, 2000, "Wide panorama"),
        (800, 600, "Small landscape"),
        (600, 800, "Small portrait"),
    ]
    
    target_width = 960
    target_height = 544
    
    print(f"Target dimensions: {target_width}x{target_height}")
    print(f"Target aspect ratio: {target_width/target_height:.3f}")
    print("=" * 70)
    
    for width, height, description in test_cases:
        # Create test image
        test_image = Image.new('RGB', (width, height), color='red')
        
        # Apply resize and crop
        result = resize_and_crop_image(test_image, target_width, target_height)
        
        # Verify result
        assert result.size == (target_width, target_height), \
            f"Expected {target_width}x{target_height}, got {result.size}"
        
        print(f"✅ {description:20s} {width:4d}x{height:4d} → {result.size[0]:4d}x{result.size[1]:4d}")
    
    print("=" * 70)
    print("All tests passed! ✅")


if __name__ == "__main__":
    test_resize_and_crop()

