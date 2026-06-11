import bpy
import os
from typing import List
from ..utils.statistics import TextureStats

def analyze_textures() -> List[TextureStats]:
    textures = []
    for img in bpy.data.images:
        # Ignore Render Results and Viewers
        if img.source in {'VIEWER', 'GENERATED'} or not img.has_data:
            continue
            
        stats = TextureStats()
        stats.name = img.name
        stats.resolution = tuple(img.size)
        stats.bit_depth = img.depth
        stats.file_format = img.file_format
        
        # Calculate VRAM: Width * Height * Channels * (BitDepth / 8)
        channels = img.channels
        width, height = stats.resolution
        bytes_per_pixel = channels * (stats.bit_depth / 8.0)
        vram_bytes = width * height * bytes_per_pixel
        
        stats.estimated_vram_mb = vram_bytes / (1024 * 1024)
        
        # Attempt to get file size
        if img.filepath:
            abs_path = bpy.path.abspath(img.filepath)
            if os.path.exists(abs_path):
                stats.file_size_mb = os.path.getsize(abs_path) / (1024 * 1024)
                
        textures.append(stats)
        
    # Sort by VRAM usage descending
    textures.sort(key=lambda t: t.estimated_vram_mb, reverse=True)
    return textures
