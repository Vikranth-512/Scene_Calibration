import bpy

class RENDERANALYZER_PT_dashboard(bpy.types.Panel):
    bl_label = "Performance Dashboard"
    bl_idname = "RENDERANALYZER_PT_dashboard"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Render Analyzer"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.render_analyzer_props
        
        row = layout.row()
        row.scale_y = 1.5
        row.operator("renderanalyzer.analyze_scene", text="Analyze Scene", icon='VIEWZOOM')
        
        if not props.has_valid_data:
            layout.label(text="Click Analyze Scene to begin.")
            return
            
        box = layout.box()
        box.label(text="Overall Complexity", icon='FILE_TICK')
        col = box.column(align=True)
        col.label(text=f"Cycles: {props.cycles_score:.1f} / 100 ({props.cycles_category})")
        col.label(text=f"Eevee: {props.eevee_score:.1f} / 100 ({props.eevee_category})")
        
        box = layout.box()
        box.label(text="Estimations", icon='TIME')
        col = box.column(align=True)
        if props.estimated_frame_time_s > 0:
            if props.confidence_score >= 0.8:
                col.label(text=f"Est. Frame Time (Benchmark): {props.estimated_frame_time_s:.1f} sec", icon='FUND')
            else:
                col.label(text=f"Est. Frame Time (Static): {props.estimated_frame_time_s:.1f} sec", icon='FILE_TEXT')
        else:
            col.label(text="Est. Frame Time: Unknown", icon='QUESTION')
            
        col.label(text=f"Est. VRAM Usage: {props.total_vram_mb:.1f} MB")
        
        layout.separator()
        layout.operator("renderanalyzer.benchmark_render", text="Run Render Benchmark", icon='RENDER_STILL')
        layout.operator("renderanalyzer.analyze_animation", text="Analyze Animation", icon='RENDER_ANIMATION')

class RENDERANALYZER_PT_hardware(bpy.types.Panel):
    bl_label = "Memory Estimates"
    bl_idname = "RENDERANALYZER_PT_hardware"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Render Analyzer"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.render_analyzer_props
        
        if not props.has_valid_data:
            return
            
        col = layout.column(align=True)
        col.label(text=f"Geometry VRAM: {props.geometry_vram_mb:.1f} MB")
        col.label(text=f"Texture VRAM: {props.texture_vram_mb:.1f} MB")
        col.label(text=f"Total VRAM: {props.total_vram_mb:.1f} MB")
        col.label(text=f"System RAM: {props.system_ram_mb:.1f} MB")

class RENDERANALYZER_PT_bottlenecks(bpy.types.Panel):
    bl_label = "Top Bottlenecks"
    bl_idname = "RENDERANALYZER_PT_bottlenecks"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Render Analyzer"

    def draw(self, context):
        layout = self.layout
        props = context.scene.render_analyzer_props
        
        if not props.has_valid_data:
            return
            
        layout.template_list("RENDERANALYZER_UL_bottlenecks", "", props, "bottlenecks", props, "active_bottleneck_index")
        
        layout.label(text="Top Textures (VRAM):")
        layout.template_list("RENDERANALYZER_UL_textures", "", props, "textures", props, "active_texture_index")

class RENDERANALYZER_PT_reports(bpy.types.Panel):
    bl_label = "Reports"
    bl_idname = "RENDERANALYZER_PT_reports"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Render Analyzer"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator("renderanalyzer.export_report", text="Export JSON Report", icon='EXPORT')
