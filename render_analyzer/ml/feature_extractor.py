import math
from typing import Dict, Any
import logging
from .schema_registry import get_schema, CURRENT_SCHEMA_VERSION

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.DEBUG)
DEBUG_BENCHMARK_PIPELINE = True

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
            features["total_base_faces"] = float(sum(m.base_face_count for m in meshes))
            faces = [m.evaluated_face_count for m in meshes]
            features["total_evaluated_faces"] = float(sum(faces))
            features["largest_mesh_faces"] = float(max(faces)) if faces else 0.0
            features["mean_mesh_faces"] = float(sum(faces) / len(faces)) if faces else 0.0
            sorted_faces = sorted(faces)
            mid = len(sorted_faces) // 2
            features["median_mesh_faces"] = float(sorted_faces[mid]) if faces else 0.0
            
            amplifications = [m.amplification_ratio for m in meshes]
            features["mean_amplification_ratio"] = float(sum(amplifications) / len(amplifications)) if amplifications else 1.0
            features["max_amplification_ratio"] = float(max(amplifications)) if amplifications else 1.0
            
            features["modifier_count"] = float(sum(1 for m in meshes if getattr(m, 'has_modifiers', False)))
            features["subdivision_count"] = float(sum(1 for m in meshes if getattr(m, 'has_subdivision', False)))
            features["geometry_nodes_count"] = float(sum(1 for m in meshes if getattr(m, 'has_geometry_nodes', False)))

        instances = getattr(snapshot, "instances", [])
        if instances:
            features["instance_count"] = float(sum(i.instance_count for i in instances))
            features["instance_face_equivalent"] = float(sum(i.total_instanced_faces for i in instances))
            
        features["instance_to_mesh_ratio"] = float(features["instance_count"] / max(features["mesh_count"], 1.0))

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
            features["total_light_energy"] = float(getattr(lighting, "total_energy", 0.0))
            features["mean_light_energy"] = float(getattr(lighting, "mean_energy", 0.0))
            features["max_light_energy"] = float(getattr(lighting, "max_energy", 0.0))

        # Volumetrics
        features["volume_count"] = float(snapshot.scene_stats.volumes)
        volumes = getattr(snapshot, "volumes", None)
        if volumes:
            features["mean_volume_density"] = float(getattr(volumes, "volumetric_cost_score", 0.0))

        # Render Settings
        render_settings = getattr(snapshot, "render_settings", None)
        if render_settings:
            features["samples"] = float(render_settings.samples)
            features["max_bounces"] = float(render_settings.max_bounces)
            features["resolution_x"] = float(render_settings.resolution_x)
            features["resolution_y"] = float(render_settings.resolution_y)
            features["resolution_pixels"] = float(render_settings.resolution_x * render_settings.resolution_y * (render_settings.resolution_percentage / 100.0))
            features["aspect_ratio"] = float(features["resolution_x"] / max(features["resolution_y"], 1.0))
            features["sample_pixel_work"] = float(features["resolution_pixels"] * features["samples"])
            
            engine = render_settings.engine.upper()
            if engine == "CYCLES":
                features["engine_cycles"] = 1.0
            elif engine == "BLENDER_EEVEE_NEXT" or engine == "BLENDER_EEVEE":
                features["engine_eevee"] = 1.0

        # Hardware
        hardware = getattr(snapshot, "hardware", None)
        if hardware:
            # Performance Tiers
            tier = hardware.performance_tier.upper()
            if tier == "ENTRY": features["tier_entry"] = 1.0
            elif tier == "MODERATE": features["tier_moderate"] = 1.0
            elif tier == "HIGH": features["tier_high"] = 1.0
            elif tier == "EXTREME": features["tier_extreme"] = 1.0
            elif tier == "CPU ONLY": features["tier_cpu_only"] = 1.0
            else: features["tier_unknown"] = 1.0

            # Hardware Details
            features["system_ram_gb"] = float(hardware.ram_gb)
            features["gpu_vram_gb"] = float(hardware.gpu_vram_gb)
            
            # === 1. Hardware Capabilities ===
            features["capability_cuda"] = 1.0 if getattr(hardware, 'capability_cuda', False) else 0.0
            features["capability_optix"] = 1.0 if getattr(hardware, 'capability_optix', False) else 0.0
            features["capability_hip"] = 1.0 if getattr(hardware, 'capability_hip', False) else 0.0
            features["capability_metal"] = 1.0 if getattr(hardware, 'capability_metal', False) else 0.0
            
            # === 2. Active Cycles Backend (one-hot) ===
            backend = getattr(hardware, "active_compute_backend", "CPU").upper()
            if backend == "CUDA": features["backend_cuda"] = 1.0
            elif backend == "OPTIX": features["backend_optix"] = 1.0
            elif backend == "HIP": features["backend_hip"] = 1.0
            elif backend == "METAL": features["backend_metal"] = 1.0
            else: features["backend_cpu"] = 1.0
            
            # === 3. Actual Render Device (one-hot) ===
            render_device = getattr(hardware, "render_device", "CPU").upper()
            if render_device == "GPU":
                features["render_device_gpu"] = 1.0
            else:
                features["render_device_cpu"] = 1.0
            
            # === 4. GPU Vendor (one-hot) ===
            vendor = getattr(hardware, "gpu_vendor", "Unknown").upper()
            if vendor == "NVIDIA": features["gpu_vendor_nvidia"] = 1.0
            elif vendor == "AMD": features["gpu_vendor_amd"] = 1.0
            elif vendor == "INTEL": features["gpu_vendor_intel"] = 1.0
            elif vendor == "APPLE": features["gpu_vendor_apple"] = 1.0
            else: features["gpu_vendor_unknown"] = 1.0
            
            # === 5. GPU Family (one-hot) ===
            family = getattr(hardware, "gpu_family", "Unknown").upper()
            if family == "GTX": features["gpu_family_gtx"] = 1.0
            elif family == "RTX": features["gpu_family_rtx"] = 1.0
            elif family == "QUADRO": features["gpu_family_quadro"] = 1.0
            elif family == "TESLA": features["gpu_family_tesla"] = 1.0
            elif family == "RX": features["gpu_family_rx"] = 1.0
            elif family == "ARC": features["gpu_family_arc"] = 1.0
            elif family == "INTEGRATED": features["gpu_family_integrated"] = 1.0
            else: features["gpu_family_unknown"] = 1.0
            
            # === 6. GPU Performance Index ===
            features["gpu_model_number"] = float(getattr(hardware, "gpu_model_number", -1.0))
            features["gpu_generation"] = float(getattr(hardware, "gpu_generation", -1.0))

        # Complexity Metrics
        cycles_score = getattr(snapshot, "cycles_score", None)
        if cycles_score:
            features["complexity_score"] = float(cycles_score.total_score)
            features["geometry_score"] = float(cycles_score.mesh_score)
            features["material_score"] = float(cycles_score.shader_score)
            features["lighting_score"] = float(cycles_score.lighting_score)
            features["volume_score"] = float(cycles_score.volume_score)

        # Benchmark
        benchmark = getattr(snapshot, "benchmark", None)
        if benchmark and benchmark.sample_times and benchmark.sample_pixels:
            times = benchmark.sample_times
            pixels = benchmark.sample_pixels
            
            if len(times) != len(pixels) or len(times) == 0:
                raise ValueError("Benchmark data exists but sample arrays are invalid or mismatched.")
                
            features["benchmark_time"] = float(sum(times))
            features["benchmark_pixels"] = float(sum(pixels))
            
            if len(times) > 1 and len(pixels) > 1:
                min_idx = pixels.index(min(pixels))
                max_idx = pixels.index(max(pixels))
                dpixels = pixels[max_idx] - pixels[min_idx]
                dtime = times[max_idx] - times[min_idx]
                if dpixels > 0:
                    tpp = dtime / dpixels
                    features["benchmark_time_per_pixel"] = float(tpp)
                    features["benchmark_fixed_overhead"] = float(times[max_idx] - pixels[max_idx] * tpp)
            elif len(times) == 1 and pixels[0] > 0:
                features["benchmark_time_per_pixel"] = float(times[0] / pixels[0])
                
            if DEBUG_BENCHMARK_PIPELINE:
                logger.debug(f"BENCHMARK FEATURES: time={features.get('benchmark_time')}, tpp={features.get('benchmark_time_per_pixel')}")
            
        # Guarantee NaN/Inf are removed
        for k, v in features.items():
            if not math.isfinite(v):
                features[k] = 0.0

        return features
