import bpy
import json
import dataclasses
from .helpers import generate_scene_fingerprint
from .statistics import SceneAnalysisSnapshot, HardwareProfile, SceneStats, CyclesComplexityScore, EeveeComplexityScore, MemoryEstimate, ObjectBottleneck, TextureStats, RenderSettingsStats

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)

def save_analysis_to_cache(scene, snapshot: SceneAnalysisSnapshot):
    """Saves the SceneAnalysisSnapshot to a custom property as a JSON string."""
    fingerprint = generate_scene_fingerprint(scene)
    
    data = {
        "fingerprint": fingerprint,
        "snapshot": dataclasses.asdict(snapshot)
    }
    
    json_str = json.dumps(data, cls=EnhancedJSONEncoder)
    scene["render_analyzer_cache"] = json_str

def load_analysis_from_cache(scene) -> SceneAnalysisSnapshot:
    """Loads and reconstructs the SceneAnalysisSnapshot from cache if the fingerprint matches."""
    if "render_analyzer_cache" not in scene:
        return None
        
    try:
        json_str = scene["render_analyzer_cache"]
        data = json.loads(json_str)
        
        current_fingerprint = generate_scene_fingerprint(scene)
        if data.get("fingerprint") != current_fingerprint:
            # Cache invalid
            return None
            
        snapshot_dict = data.get("snapshot", {})
        
        # Reconstruct Dataclasses
        snapshot = SceneAnalysisSnapshot(
            hardware=HardwareProfile(**snapshot_dict.get("hardware", {})),
            scene_stats=SceneStats(**snapshot_dict.get("scene_stats", {})),
            cycles_score=CyclesComplexityScore(**snapshot_dict.get("cycles_score", {})),
            eevee_score=EeveeComplexityScore(**snapshot_dict.get("eevee_score", {})),
            memory_estimate=MemoryEstimate(**snapshot_dict.get("memory_estimate", {})),
            top_bottlenecks=[ObjectBottleneck(**b) for b in snapshot_dict.get("top_bottlenecks", [])],
            top_textures=[TextureStats(**t) for t in snapshot_dict.get("top_textures", [])],
            render_settings=RenderSettingsStats(**snapshot_dict.get("render_settings", {}))
        )
        return snapshot
        
    except Exception as e:
        print(f"Render Analyzer: Error loading cache: {e}")
        return None

def clear_cache(scene):
    """Clears the analysis cache."""
    if "render_analyzer_cache" in scene:
        del scene["render_analyzer_cache"]
