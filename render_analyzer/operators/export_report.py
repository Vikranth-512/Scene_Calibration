import bpy
import json
import csv
import os
from bpy_extras.io_utils import ExportHelper

class RENDERANALYZER_OT_export_report(bpy.types.Operator, ExportHelper):
    """Export Analysis Report"""
    bl_idname = "renderanalyzer.export_report"
    bl_label = "Export Report"
    
    filename_ext = ".json"
    
    filter_glob: bpy.props.StringProperty(
        default="*.json;*.csv",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        scene = context.scene
        if "render_analyzer_cache" not in scene:
            self.report({'ERROR'}, "No analysis data to export. Please analyze scene first.")
            return {'CANCELLED'}
            
        data_str = scene["render_analyzer_cache"]
        
        ext = os.path.splitext(self.filepath)[1].lower()
        if ext == '.json':
            with open(self.filepath, 'w') as f:
                f.write(data_str)
        elif ext == '.csv':
            self.report({'WARNING'}, "CSV export not fully implemented, saving as JSON")
            with open(self.filepath, 'w') as f:
                f.write(data_str)
                
        self.report({'INFO'}, f"Exported to {self.filepath}")
        return {'FINISHED'}
