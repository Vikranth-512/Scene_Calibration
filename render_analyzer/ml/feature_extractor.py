import math
from typing import Dict, Any
from .schema_registry import get_schema, CURRENT_SCHEMA_VERSION

class FeatureExtractor:
    @staticmethod
    def extract(snapshot: Any, schema_version: int = CURRENT_SCHEMA_VERSION) -> Dict[str, float]:
        """
        Pure function. Extracts features from a SceneAnalysisSnapshot.
        Does not interact with bpy, context, or scene.
        """
        schema_info = get_schema(schema_version)
        features_meta = schema_info["features"]
        
        # Initialize with defaults
        features = {k: float(v["default"]) for k, v in features_meta.items()}

        if not snapshot:
            return features

        # Geometry
        features["total_evaluated_faces"] = float(snapshot.scene_stats.total_faces)
        features["total_vertices"] = float(snapshot.scene_stats.total_vertices)
        features["mesh_count"] = float(snapshot.scene_stats.meshes)
        
        meshes = getattr(snapshot, "meshes", [])
        if meshes:
            faces = [m.evaluated_face_count for m in meshes]
            features["largest_mesh_faces"] = float(max(faces)) if faces else 0.0
            features["mean_mesh_faces"] = float(sum(faces) / len(faces)) if faces else 0.0
            sorted_faces = sorted(faces)
            mid = len(sorted_faces) // 2
            features["median_mesh_faces"] = float(sorted_faces[mid]) if faces else 0.0
            features["modifier_count"] = float(sum(1 for m in meshes if getattr(m, 'has_modifiers', False)))
            features["subdivision_count"] = float(sum(1 for m in meshes if getattr(m, 'has_subdivision', False)))
            features["geometry_nodes_count"] = float(sum(1 for m in meshes if getattr(m, 'has_geometry_nodes', False)))

        instances = getattr(snapshot, "instances", [])
        if instances:
            features["instance_count"] = float(sum(i.instance_count for i in instances))
            features["instance_face_equivalent"] = float(sum(i.total_instanced_faces for i in instances))

        # Materials
        features["material_count"] = float(snapshot.scene_stats.materials)
        materials = getattr(snapshot, "materials", [])
        if materials:
            features["glass_material_count"] = float(sum(m.glass_count for m in materials))
            features["volume_material_count"] = float(sum(m.volume_scatter_count + m.volume_absorption_count for m in materials))
            features["displacement_material_count"] = float(sum(m.displacement_count for m in materials))
            
            nodes_counts = [getattr(m, 'shader_complexity_score', 0) for m in materials]
            features["total_shader_nodes"] = float(sum(nodes_counts))
            features["average_shader_nodes"] = float(sum(nodes_counts) / len(nodes_counts)) if nodes_counts else 0.0
            features["max_shader_nodes"] = float(max(nodes_counts)) if nodes_counts else 0.0

        # Textures
        features["texture_count"] = float(snapshot.scene_stats.textures)
        mem_est = getattr(snapshot, "memory_estimate", None)
        if mem_est:
            features["texture_memory_mb"] = float(mem_est.texture_vram_mb)
            features["vram_estimate_mb"] = float(mem_est.total_vram_mb)
            
        textures = getattr(snapshot, "top_textures", [])
        if textures:
            pixels = [t.resolution[0] * t.resolution[1] for t in textures]
            features["largest_texture_pixels"] = float(max(pixels)) if pixels else 0.0
            features["mean_texture_pixels"] = float(sum(pixels) / len(pixels)) if pixels else 0.0

        # Lighting
        features["light_count"] = float(snapshot.scene_stats.lights)
        lighting = getattr(snapshot, "lighting", None)
        if lighting:
            features["sun_count"] = float(lighting.sun_lights)
            features["point_count"] = float(lighting.point_lights)
            features["spot_count"] = float(lighting.spot_lights)
            features["area_count"] = float(lighting.area_lights)
            features["emissive_material_count"] = float(lighting.emissive_objects)
            features["hdri_count"] = 1.0 if lighting.hdri_environment else 0.0

        # Volumetrics
        features["volume_count"] = float(snapshot.scene_stats.volumes)
        # Note: volume_world_space_m3 and density might not be directly in snapshot.volumes.
        # Fallback to defaults or what is available
        volumes = getattr(snapshot, "volumes", None)
        if volumes:
            # We use volumetric_cost_score as a proxy if explicit fields don't exist
            features["mean_volume_density"] = float(getattr(volumes, "volumetric_cost_score", 0.0))

        # Render Settings
        render_settings = getattr(snapshot, "render_settings", None)
        if render_settings:
            features["samples"] = float(render_settings.samples)
            features["max_bounces"] = float(render_settings.max_bounces)
            features["resolution_x"] = float(render_settings.resolution_x)
            features["resolution_y"] = float(render_settings.resolution_y)
            features["resolution_pixels"] = float(render_settings.resolution_x * render_settings.resolution_y * (render_settings.resolution_percentage / 100.0))
            
            engine = render_settings.engine.upper()
            if engine == "CYCLES":
                features["engine_cycles"] = 1.0
            elif engine == "BLENDER_EEVEE_NEXT" or engine == "BLENDER_EEVEE":
                features["engine_eevee"] = 1.0

        # Hardware Performance Tiers
        hardware = getattr(snapshot, "hardware", None)
        if hardware:
            tier = hardware.performance_tier.upper()
            if tier == "ENTRY": features["tier_entry"] = 1.0
            elif tier == "MODERATE": features["tier_moderate"] = 1.0
            elif tier == "HIGH": features["tier_high"] = 1.0
            elif tier == "EXTREME": features["tier_extreme"] = 1.0
            elif tier == "CPU ONLY": features["tier_cpu_only"] = 1.0
            else: features["tier_unknown"] = 1.0

            features["system_ram_gb"] = float(hardware.ram_gb)
            features["gpu_vram_gb"] = float(hardware.gpu_vram_gb)
            
            features["optix_enabled"] = 1.0 if getattr(hardware, 'optix_enabled', False) else 0.0
            features["cuda_enabled"] = 1.0 if getattr(hardware, 'cuda_enabled', False) else 0.0
            features["metal_enabled"] = 1.0 if getattr(hardware, 'metal_enabled', False) else 0.0
            features["hip_enabled"] = 1.0 if getattr(hardware, 'hip_enabled', False) else 0.0
            
            backend = getattr(hardware, "active_compute_backend", "CPU").upper()
            if backend == "CUDA": features["backend_cuda"] = 1.0
            elif backend == "OPTIX": features["backend_optix"] = 1.0
            elif backend == "HIP": features["backend_hip"] = 1.0
            elif backend == "METAL": features["backend_metal"] = 1.0
            else: features["backend_cpu"] = 1.0

        # Complexity Metrics
        cycles_score = getattr(snapshot, "cycles_score", None)
        if cycles_score:
            features["complexity_score"] = float(cycles_score.total_score)
            features["geometry_score"] = float(cycles_score.mesh_score)
            features["material_score"] = float(cycles_score.shader_score)
            features["lighting_score"] = float(cycles_score.lighting_score)
            features["volume_score"] = float(cycles_score.volume_score)
            
        # Guarantee NaN/Inf are removed
        for k, v in features.items():
            if not math.isfinite(v):
                features[k] = 0.0

        return features
