import bpy
from ..estimation.benchmark_engine import BenchmarkEngine

class RENDERANALYZER_OT_benchmark_render(bpy.types.Operator):
    """Run a border-region benchmark to estimate render times"""
    bl_idname = "renderanalyzer.benchmark_render"
    bl_label = "Benchmark Render"
    
    _timer = None
    _engine = None
    _regions = [
        (0.0, 0.1, 0.9, 1.0), # Top Left
        (0.45, 0.55, 0.45, 0.55), # Center
        (0.9, 1.0, 0.9, 1.0), # Top Right
        (0.0, 0.1, 0.0, 0.1), # Bottom Left
        (0.9, 1.0, 0.0, 0.1)  # Bottom Right
    ]
    _current_region = 0
    _times = []

    def modal(self, context, event):
        if event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if self._current_region < len(self._regions):
                r = self._regions[self._current_region]
                self._engine.apply_render_border(context.scene, r[0], r[1], r[2], r[3])
                
                # Render blocks, but it's small so UI unlocks between regions
                duration = self._engine.render_sample()
                self._times.append(duration)
                
                self._current_region += 1
                # Trigger a UI redraw
                for window in context.window_manager.windows:
                    for area in window.screen.areas:
                        area.tag_redraw()
            else:
                self.finish(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        self._engine = BenchmarkEngine()
        self._engine.save_current_settings(context.scene)
        self._current_region = 0
        self._times = []
        
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        self.report({'INFO'}, "Starting Benchmark...")
        return {'RUNNING_MODAL'}

    def finish(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self._engine.restore_settings(context.scene)
        
        avg_time = sum(self._times) / len(self._times)
        context.scene.render_analyzer_props.last_benchmark_time = avg_time
        
        # Trigger an update of the estimate
        bpy.ops.renderanalyzer.analyze_scene()
        
        self.report({'INFO'}, f"Benchmark Complete. Avg region time: {avg_time:.2f}s")

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self._engine.restore_settings(context.scene)
        self.report({'WARNING'}, "Benchmark Cancelled")
