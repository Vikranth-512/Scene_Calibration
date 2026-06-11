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
]

modulesFullNames = {}
for currentModuleName in modulesNames:
    modulesFullNames[currentModuleName] = f"{__name__}.{currentModuleName}"

for currentModuleFullName in modulesFullNames.values():
    if currentModuleFullName in sys.modules:
        importlib.reload(sys.modules[currentModuleFullName])
else:
    from . import utils, analyzers, estimation, ui, operators

from .ui.properties import BottleneckItem, TextureItem, RenderAnalyzerProperties
from .ui.lists import RENDERANALYZER_UL_bottlenecks, RENDERANALYZER_UL_textures
from .ui.panels import RENDERANALYZER_PT_dashboard, RENDERANALYZER_PT_hardware, RENDERANALYZER_PT_bottlenecks, RENDERANALYZER_PT_reports
from .operators.analyze_scene import RENDERANALYZER_OT_analyze_scene
from .operators.analyze_animation import RENDERANALYZER_OT_analyze_animation
from .operators.benchmark_render import RENDERANALYZER_OT_benchmark_render
from .operators.export_report import RENDERANALYZER_OT_export_report

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
    RENDERANALYZER_OT_analyze_scene,
    RENDERANALYZER_OT_analyze_animation,
    RENDERANALYZER_OT_benchmark_render,
    RENDERANALYZER_OT_export_report,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.render_analyzer_props = bpy.props.PointerProperty(type=RenderAnalyzerProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.render_analyzer_props

if __name__ == "__main__":
    register()
