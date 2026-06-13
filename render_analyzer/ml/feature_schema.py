FEATURES_V1 = {
    # Geometry
    "total_evaluated_faces": {"type": float, "default": 0.0},
    "total_vertices": {"type": float, "default": 0.0},
    "mesh_count": {"type": float, "default": 0.0},
    "largest_mesh_faces": {"type": float, "default": 0.0},
    "mean_mesh_faces": {"type": float, "default": 0.0},
    "median_mesh_faces": {"type": float, "default": 0.0},
    "modifier_count": {"type": float, "default": 0.0},
    "subdivision_count": {"type": float, "default": 0.0},
    "geometry_nodes_count": {"type": float, "default": 0.0},
    "instance_count": {"type": float, "default": 0.0},
    "instance_face_equivalent": {"type": float, "default": 0.0},

    # Materials
    "material_count": {"type": float, "default": 0.0},
    "glass_material_count": {"type": float, "default": 0.0},
    "volume_material_count": {"type": float, "default": 0.0},
    "displacement_material_count": {"type": float, "default": 0.0},
    "total_shader_nodes": {"type": float, "default": 0.0},
    "average_shader_nodes": {"type": float, "default": 0.0},
    "max_shader_nodes": {"type": float, "default": 0.0},

    # Textures
    "texture_count": {"type": float, "default": 0.0},
    "texture_memory_mb": {"type": float, "default": 0.0},
    "vram_estimate_mb": {"type": float, "default": 0.0},
    "largest_texture_pixels": {"type": float, "default": 0.0},
    "mean_texture_pixels": {"type": float, "default": 0.0},

    # Lighting
    "light_count": {"type": float, "default": 0.0},
    "sun_count": {"type": float, "default": 0.0},
    "point_count": {"type": float, "default": 0.0},
    "spot_count": {"type": float, "default": 0.0},
    "area_count": {"type": float, "default": 0.0},
    "emissive_material_count": {"type": float, "default": 0.0},
    "hdri_count": {"type": float, "default": 0.0},

    # Volumetrics
    "volume_count": {"type": float, "default": 0.0},
    "volume_world_space_m3": {"type": float, "default": 0.0},
    "mean_volume_density": {"type": float, "default": 0.0},
    "max_volume_density": {"type": float, "default": 0.0},

    # Render Settings
    "samples": {"type": float, "default": 0.0},
    "max_bounces": {"type": float, "default": 0.0},
    "resolution_x": {"type": float, "default": 0.0},
    "resolution_y": {"type": float, "default": 0.0},
    "resolution_pixels": {"type": float, "default": 0.0},
    "engine_cycles": {"type": float, "default": 0.0},
    "engine_eevee": {"type": float, "default": 0.0},

    # Hardware Performance Tiers
    "tier_entry": {"type": float, "default": 0.0},
    "tier_moderate": {"type": float, "default": 0.0},
    "tier_high": {"type": float, "default": 0.0},
    "tier_extreme": {"type": float, "default": 0.0},
    "tier_unknown": {"type": float, "default": 0.0},
    "tier_cpu_only": {"type": float, "default": 0.0},

    # Hardware Details
    "system_ram_gb": {"type": float, "default": 0.0},
    "gpu_vram_gb": {"type": float, "default": 0.0},

    # Hardware Engine Options
    "optix_enabled": {"type": float, "default": 0.0},
    "cuda_enabled": {"type": float, "default": 0.0},
    "metal_enabled": {"type": float, "default": 0.0},
    "hip_enabled": {"type": float, "default": 0.0},
    
    # Active Compute Backend
    "backend_cpu": {"type": float, "default": 0.0},
    "backend_cuda": {"type": float, "default": 0.0},
    "backend_optix": {"type": float, "default": 0.0},
    "backend_hip": {"type": float, "default": 0.0},
    "backend_metal": {"type": float, "default": 0.0},

    # Complexity Metrics
    "complexity_score": {"type": float, "default": 0.0},
    "geometry_score": {"type": float, "default": 0.0},
    "material_score": {"type": float, "default": 0.0},
    "lighting_score": {"type": float, "default": 0.0},
    "volume_score": {"type": float, "default": 0.0},
}

FEATURE_ORDER_V1 = tuple(FEATURES_V1.keys())
