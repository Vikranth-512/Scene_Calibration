import bpy
from ..utils.scene_cache import clear_cache
from ..core.session_manager import AnalysisSession

class RENDERANALYZER_OT_clear_cache(bpy.types.Operator):
    """Clear the analysis cache and reset the addon"""
    bl_idname = "renderanalyzer.clear_cache"
    bl_label = "Clear Cache & Reset"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        
        # Clear the internal cache
        clear_cache(scene)
        
        # Reset session
        AnalysisSession.set_snapshot(None)
        AnalysisSession.set_feature_vector(None)
        
        # Reset UI properties
        scene.render_analyzer_props.has_valid_data = False
        scene.render_analyzer_props.benchmark_data = ""
        
        self.report({'INFO'}, "Render Analyzer: Cache cleared and add-on reset.")
        
        # Force UI redraw
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
                    
        return {'FINISHED'}
