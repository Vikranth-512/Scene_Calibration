from typing import List
from ..utils.statistics import MemoryEstimate, MeshStats, TextureStats, VolumeStats

def estimate_memory(
    meshes: List[MeshStats],
    textures: List[TextureStats],
    volumes: VolumeStats
) -> MemoryEstimate:
    est = MemoryEstimate()
    
    # Geometry VRAM: Very rough estimate (e.g. 150 bytes per face with normals, UVs, etc.)
    total_faces = sum(m.face_count for m in meshes)
    est.geometry_vram_mb = (total_faces * 150) / (1024 * 1024)
    
    # Texture VRAM
    est.texture_vram_mb = sum(t.estimated_vram_mb for t in textures)
    
    # Volume VRAM: Arbitrary 50MB per volume as baseline
    est.volume_vram_mb = volumes.volume_count * 50.0
    
    # Total VRAM (including base overhead for Blender / OS)
    base_vram_overhead = 300.0
    est.total_vram_mb = est.geometry_vram_mb + est.texture_vram_mb + est.volume_vram_mb + base_vram_overhead
    
    # System RAM (usually mirrors VRAM + application overhead)
    base_ram_overhead = 1024.0
    est.total_system_ram_mb = est.total_vram_mb * 1.2 + base_ram_overhead
    
    return est
