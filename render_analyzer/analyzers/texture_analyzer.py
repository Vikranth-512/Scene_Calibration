import bpy
import os
from typing import List
from ..utils.statistics import TextureStats

def analyze_textures() -> List[TextureStats]:
    textures = []
    for img in bpy.data.images:
        # Ignore Render Results and Viewers
        if img.source in {'VIEWER', 'GENERATED'}:
            continue
            
        if img.size[0] == 0 or img.size[1] == 0:
            continue
            
        stats = TextureStats()
        stats.name = img.name
        stats.resolution = tuple(img.size)
        stats.bit_depth = img.depth
        stats.file_format = img.file_format
        
        # Calculate VRAM: GPUs pack textures differently than disk
        channels = img.channels
        width, height = stats.resolution
        
        if stats.file_format in {'OPEN_EXR', 'OPEN_EXR_MULTILAYER', 'HDR'}:
            bytes_per_pixel = channels * 4.0 # 32-bit floats
        else:
            bytes_per_pixel = 4.0 # Often unpacked to RGBA32 (8-bit per channel)
            
        raw_vram_bytes = width * height * bytes_per_pixel
        
        # Add 33% overhead for Mipmaps
        effective_vram_bytes = raw_vram_bytes * 1.33
        
        stats.estimated_vram_mb = effective_vram_bytes / (1024 * 1024)
        
        # Attempt to get file size
        if img.filepath:
            abs_path = bpy.path.abspath(img.filepath)
            if os.path.exists(abs_path):
                stats.file_size_mb = os.path.getsize(abs_path) / (1024 * 1024)
                
        textures.append(stats)
        
    # Sort by VRAM usage descending
    textures.sort(key=lambda t: t.estimated_vram_mb, reverse=True)
    return textures
