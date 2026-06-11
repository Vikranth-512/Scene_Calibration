import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, CollectionProperty, PointerProperty
from ..utils.statistics import SceneAnalysisSnapshot

class BottleneckItem(bpy.types.PropertyGroup):
    object_name: StringProperty(name="Object")
    impact_score: FloatProperty(name="Impact")
    contribution_percent: FloatProperty(name="Percent")
    primary_cause: StringProperty(name="Cause")

class TextureItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Name")
    estimated_vram_mb: FloatProperty(name="VRAM (MB)")

class RenderAnalyzerProperties(bpy.types.PropertyGroup):
    # Performance Dashboard / Complexity
    cycles_score: FloatProperty(name="Cycles Score")
    eevee_score: FloatProperty(name="Eevee Score")
    cycles_category: StringProperty(name="Cycles Category", default="Unknown")
    eevee_category: StringProperty(name="Eevee Category", default="Unknown")
    
    # Memory
    geometry_vram_mb: FloatProperty(name="Geometry VRAM")
    texture_vram_mb: FloatProperty(name="Texture VRAM")
    total_vram_mb: FloatProperty(name="Total VRAM")
    system_ram_mb: FloatProperty(name="System RAM")
    
    # Benchmarking
    last_benchmark_time: FloatProperty(name="Benchmark Avg", default=0.0)
    estimated_frame_time_s: FloatProperty(name="Est. Frame Time (s)", default=0.0)
    confidence_score: FloatProperty(name="Confidence Score", default=0.0)
    
    # Collections for UILists
    bottlenecks: CollectionProperty(type=BottleneckItem)
    active_bottleneck_index: IntProperty()
    
    textures: CollectionProperty(type=TextureItem)
    active_texture_index: IntProperty()
    
    has_valid_data: bpy.props.BoolProperty(default=False)

    def update_from_snapshot(self, snapshot: SceneAnalysisSnapshot):
        self.cycles_score = snapshot.cycles_score.total_score
        self.eevee_score = snapshot.eevee_score.total_score
        self.cycles_category = snapshot.cycles_score.category
        self.eevee_category = snapshot.eevee_score.category
        
        self.geometry_vram_mb = snapshot.memory_estimate.geometry_vram_mb
        self.texture_vram_mb = snapshot.memory_estimate.texture_vram_mb
        self.total_vram_mb = snapshot.memory_estimate.total_vram_mb
        self.system_ram_mb = snapshot.memory_estimate.total_system_ram_mb
        
        self.bottlenecks.clear()
        for b in snapshot.top_bottlenecks:
            item = self.bottlenecks.add()
            item.object_name = b.object_name
            item.impact_score = b.impact_score
            item.contribution_percent = b.contribution_percent
            item.primary_cause = b.primary_cause
            
        self.textures.clear()
        for t in snapshot.top_textures:
            item = self.textures.add()
            item.name = t.name
            item.estimated_vram_mb = t.estimated_vram_mb
            
        self.has_valid_data = True
