import bpy

class RENDERANALYZER_UL_bottlenecks(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.label(text=item.object_name, icon='OBJECT_DATA')
            row.label(text=f"Score: {item.impact_score:.1f}")
            row.label(text=item.primary_cause)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.object_name)

class RENDERANALYZER_UL_textures(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.label(text=item.name, icon='IMAGE_DATA')
            row.label(text=f"{item.estimated_vram_mb:.1f} MB")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.name)
