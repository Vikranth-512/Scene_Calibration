bl_info = {
    "name": "Render Performance Analyzer",
    "author": "Antigravity",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Render Analyzer",
    "description": "Comprehensive render-performance analysis and estimation tool.",
    "warning": "",
    "doc_url": "",
    "category": "Render",
}

import bpy
import importlib
import sys

# Handling module reloading
modulesNames = [
    # Data & Utils
    "utils.statistics",
    "utils.helpers",
    "utils.scene_cache",
    
    # Analyzers
    "analyzers.hardware_analyzer",
    "analyzers.texture_analyzer",
    "analyzers.mesh_analyzer",
    "analyzers.scene_analyzer",
    "analyzers.modifier_analyzer",
    "analyzers.geometry_nodes_analyzer",
    "analyzers.material_analyzer",
    "analyzers.lighting_analyzer",
    "analyzers.volume_analyzer",
    "analyzers.render_settings_analyzer",
    "analyzers.animation_analyzer",
    
    # Estimation
    "estimation.complexity_score",
    "estimation.memory_estimator",
    "estimation.benchmark_engine",
    "estimation.render_time_estimator",
    
    # UI & Operators
    "ui.properties",
    "ui.lists",
    "ui.panels",
    "operators.analyze_scene",
    "operators.analyze_animation",
    "operators.benchmark_render",
    "operators.export_report",
    "operators.export_ml_features",
    "operators.clear_cache",
    
    # ML
    "ml.schema_registry",
    "ml.feature_schema",
    "ml.dataset_row",
    "ml.feature_extractor",
    "ml.dataset_manager",
    "ml.dataset_export",
    "ml.telemetry",
    
    # Core
    "core.session_manager",
]

modulesFullNames = {}
for currentModuleName in modulesNames:
    modulesFullNames[currentModuleName] = f"{__name__}.{currentModuleName}"

for currentModuleFullName in modulesFullNames.values():
    if currentModuleFullName in sys.modules:
        importlib.reload(sys.modules[currentModuleFullName])
else:
    from . import utils, analyzers, estimation, ui, operators, ml, core

from .ui.properties import BottleneckItem, TextureItem, RenderAnalyzerProperties
from .ui.lists import RENDERANALYZER_UL_bottlenecks, RENDERANALYZER_UL_textures
from .ui.panels import RENDERANALYZER_PT_dashboard, RENDERANALYZER_PT_hardware, RENDERANALYZER_PT_bottlenecks, RENDERANALYZER_PT_reports, RENDERANALYZER_PT_ml_tools
from .operators.analyze_scene import RENDERANALYZER_OT_analyze_scene
from .operators.analyze_animation import RENDERANALYZER_OT_analyze_animation
from .operators.benchmark_render import RENDERANALYZER_OT_benchmark_render
from .operators.export_report import RENDERANALYZER_OT_export_report
from .operators.export_ml_features import RENDERANALYZER_OT_export_ml_features
from .operators.clear_cache import RENDERANALYZER_OT_clear_cache

classes = (
    BottleneckItem,
    TextureItem,
    RenderAnalyzerProperties,
    RENDERANALYZER_UL_bottlenecks,
    RENDERANALYZER_UL_textures,
    RENDERANALYZER_PT_dashboard,
    RENDERANALYZER_PT_hardware,
    RENDERANALYZER_PT_bottlenecks,
    RENDERANALYZER_PT_reports,
    RENDERANALYZER_PT_ml_tools,
    RENDERANALYZER_OT_analyze_scene,
    RENDERANALYZER_OT_analyze_animation,
    RENDERANALYZER_OT_benchmark_render,
    RENDERANALYZER_OT_export_report,
    RENDERANALYZER_OT_export_ml_features,
    RENDERANALYZER_OT_clear_cache,
)

from .reporting.telemetry_handler import register_telemetry, unregister_telemetry
from .ml.telemetry import register_ml_telemetry, unregister_ml_telemetry
from .utils.helpers import generate_scene_fingerprint

@bpy.app.handlers.persistent
def depsgraph_update_cache_invalidator(scene, depsgraph):
    # Skip invalidation entirely while a benchmark is running — the benchmark
    # itself modifies render borders/samples which would trigger this handler
    # and wipe benchmark_data before the estimator can consume it.
    from .estimation.benchmark_engine import BenchmarkEngine as _BE
    if _BE.is_benchmarking:
        return
        
    # Only invalidate if we currently have valid data
    if not getattr(scene, 'render_analyzer_props', None) or not scene.render_analyzer_props.has_valid_data:
        return
        
    # Check strict SHA256 fingerprint
    current_hash = generate_scene_fingerprint(scene)
    if "render_analyzer_cache" in scene:
        import json
        try:
            data = json.loads(scene["render_analyzer_cache"])
            if data.get("fingerprint") != current_hash:
                # Content changed! Invalidate UI and clear old benchmark.
                scene.render_analyzer_props.has_valid_data = False
                scene.render_analyzer_props.benchmark_data = ""
        except:
            pass

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.render_analyzer_props = bpy.props.PointerProperty(type=RenderAnalyzerProperties)
    register_telemetry()
    register_ml_telemetry()
    if depsgraph_update_cache_invalidator not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_cache_invalidator)

def unregister():
    if depsgraph_update_cache_invalidator in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_cache_invalidator)
    unregister_telemetry()
    unregister_ml_telemetry()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.render_analyzer_props

if __name__ == "__main__":
    register()

