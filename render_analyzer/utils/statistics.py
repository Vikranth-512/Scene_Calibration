import dataclasses
from typing import List, Dict, Optional, Any

@dataclasses.dataclass
class HardwareProfile:
    cpu_name: str = "Unknown"
    ram_gb: float = 0.0
    gpu_names: List[str] = dataclasses.field(default_factory=list)
    gpu_vendor: str = "Unknown"
    performance_tier: str = "Unknown"
    gpu_vram_gb: float = -1.0

    # Hardware Capabilities (what Blender detects as available)
    capability_cuda: bool = False
    capability_optix: bool = False
    capability_hip: bool = False
    capability_metal: bool = False

    # Active Cycles Backend (cprefs.compute_device_type)
    active_compute_backend: str = "CPU"

    # Actual Render Device (scene.cycles.device)
    render_device: str = "CPU"

    # GPU Identity
    gpu_family: str = "Unknown"
    gpu_model_number: float = -1.0
    gpu_generation: float = -1.0

@dataclasses.dataclass
class TextureStats:
    name: str = ""
    resolution: tuple = (0, 0)
    bit_depth: int = 8
    file_format: str = ""
    file_size_mb: float = 0.0
    estimated_vram_mb: float = 0.0

@dataclasses.dataclass
class InstanceStats:
    base_object_name: str = ""
    instance_count: int = 0
    total_instanced_faces: int = 0

@dataclasses.dataclass
class MeshStats:
    object_name: str = ""
    vertex_count: int = 0
    edge_count: int = 0
    face_count: int = 0
    base_face_count: int = 0
    evaluated_face_count: int = 0
    amplification_ratio: float = 1.0
    triangle_count: int = 0
    ngon_count: int = 0
    is_instanced: bool = False
    has_modifiers: bool = False
    has_subdivision: bool = False
    has_geometry_nodes: bool = False
    complexity_score: str = "Low"

@dataclasses.dataclass
class MaterialStats:
    name: str = ""
    principled_count: int = 0
    glass_count: int = 0
    refraction_count: int = 0
    volume_scatter_count: int = 0
    volume_absorption_count: int = 0
    emission_count: int = 0
    noise_count: int = 0
    voronoi_count: int = 0
    musgrave_count: int = 0
    wave_count: int = 0
    mix_shader_count: int = 0
    mix_rgb_count: int = 0
    displacement_count: int = 0
    bump_count: int = 0
    normal_map_count: int = 0
    shader_complexity_score: int = 0

@dataclasses.dataclass
class VolumeStats:
    volume_count: int = 0
    volumetric_cost_score: int = 0

@dataclasses.dataclass
class LightingStats:
    point_lights: int = 0
    sun_lights: int = 0
    area_lights: int = 0
    spot_lights: int = 0
    hdri_environment: bool = False
    emissive_objects: int = 0
    shadow_casting_lights: int = 0
    lighting_cost_score: int = 0
    total_energy: float = 0.0
    mean_energy: float = 0.0
    max_energy: float = 0.0

@dataclasses.dataclass
class BenchmarkStats:
    sample_times: List[float] = dataclasses.field(default_factory=list)
    sample_pixels: List[int] = dataclasses.field(default_factory=list)

@dataclasses.dataclass
class SceneStats:
    total_objects: int = 0
    visible_objects: int = 0
    hidden_objects: int = 0
    meshes: int = 0
    lights: int = 0
    cameras: int = 0
    curves: int = 0
    volumes: int = 0
    materials: int = 0
    textures: int = 0
    instances: int = 0
    collections: int = 0
    geometry_node_objects: int = 0
    particle_systems: int = 0
    hair_systems: int = 0
    total_vertices: int = 0
    total_edges: int = 0
    total_faces: int = 0
    total_triangles: int = 0
    bounds_min: tuple = (0,0,0)
    bounds_max: tuple = (0,0,0)

@dataclasses.dataclass
class RenderSettingsStats:
    engine: str = "CYCLES"
    resolution_x: int = 1920
    resolution_y: int = 1080
    resolution_percentage: int = 100
    samples: int = 128
    adaptive_sampling: bool = False
    max_bounces: int = 12
    diffuse_bounces: int = 4
    glossy_bounces: int = 4
    transmission_bounces: int = 12
    caustics_reflective: bool = False
    caustics_refractive: bool = False
    denoising: bool = False
    motion_blur: bool = False
    depth_of_field: bool = False
    render_settings_cost_score: int = 0

@dataclasses.dataclass
class CyclesComplexityScore:
    mesh_score: float = 0.0
    modifier_score: float = 0.0
    shader_score: float = 0.0
    lighting_score: float = 0.0
    volume_score: float = 0.0
    render_settings_score: float = 0.0
    total_score: float = 0.0
    category: str = "Light"

@dataclasses.dataclass
class EeveeComplexityScore:
    mesh_score: float = 0.0
    modifier_score: float = 0.0
    shader_score: float = 0.0
    lighting_score: float = 0.0
    volume_score: float = 0.0
    render_settings_score: float = 0.0
    total_score: float = 0.0
    category: str = "Light"

@dataclasses.dataclass
class MemoryEstimate:
    geometry_vram_mb: float = 0.0
    texture_vram_mb: float = 0.0
    volume_vram_mb: float = 0.0
    total_vram_mb: float = 0.0
    total_system_ram_mb: float = 0.0

@dataclasses.dataclass
class ObjectBottleneck:
    object_name: str = ""
    impact_score: float = 0.0
    contribution_percent: float = 0.0
    primary_cause: str = ""

@dataclasses.dataclass
class SceneAnalysisSnapshot:
    hardware: HardwareProfile = dataclasses.field(default_factory=HardwareProfile)
    scene_stats: SceneStats = dataclasses.field(default_factory=SceneStats)
    cycles_score: CyclesComplexityScore = dataclasses.field(default_factory=CyclesComplexityScore)
    eevee_score: EeveeComplexityScore = dataclasses.field(default_factory=EeveeComplexityScore)
    memory_estimate: MemoryEstimate = dataclasses.field(default_factory=MemoryEstimate)
    top_bottlenecks: List[ObjectBottleneck] = dataclasses.field(default_factory=list)
    top_textures: List[TextureStats] = dataclasses.field(default_factory=list)
    render_settings: RenderSettingsStats = dataclasses.field(default_factory=RenderSettingsStats)
    instances: List[InstanceStats] = dataclasses.field(default_factory=list)
    meshes: List[MeshStats] = dataclasses.field(default_factory=list)
    materials: List[MaterialStats] = dataclasses.field(default_factory=list)
    lighting: LightingStats = dataclasses.field(default_factory=LightingStats)
    volumes: VolumeStats = dataclasses.field(default_factory=VolumeStats)
    benchmark: BenchmarkStats = dataclasses.field(default_factory=BenchmarkStats)

    def to_tensor(self):
        """
        ML Readiness: Converts the snapshot into a fixed-size numpy array suitable for model training.
        """
        try:
            import numpy as np
        except ImportError:
            return None

        # GPU Tier Mapping
        tier_map = {"Entry": 0, "Moderate": 1, "High": 2, "Extreme": 3, "Unknown": -1, "CPU Only": -2}
        tier_val = tier_map.get(self.hardware.performance_tier, -1)

        # Build feature vector
        vector = [
            float(self.scene_stats.total_faces),
            float(sum(m.evaluated_face_count for m in self.meshes)),
            float(sum(i.total_instanced_faces for i in self.instances)),
            float(self.cycles_score.shader_score),
            float(self.memory_estimate.texture_vram_mb),
            float(self.cycles_score.volume_score),
            float(self.cycles_score.lighting_score),
            float(self.render_settings.samples),
            float(self.render_settings.resolution_x * self.render_settings.resolution_y * (self.render_settings.resolution_percentage / 100.0)),
            float(tier_val),
            float(self.hardware.ram_gb)
        ]
        return np.array(vector, dtype=np.float32)
