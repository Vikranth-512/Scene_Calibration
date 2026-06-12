import bpy
import time

class BenchmarkEngine:
    # Global flag so depsgraph invalidator can skip during benchmarking
    is_benchmarking = False
    
    def __init__(self):
        self.original_settings = {}

    def save_current_settings(self, scene):
        self.original_settings = {
            "use_border": scene.render.use_border,
            "border_min_x": scene.render.border_min_x,
            "border_max_x": scene.render.border_max_x,
            "border_min_y": scene.render.border_min_y,
            "border_max_y": scene.render.border_max_y,
            "use_crop_to_border": scene.render.use_crop_to_border,
            "samples": scene.cycles.samples if scene.render.engine == 'CYCLES' else getattr(scene.eevee, "taa_render_samples", 64)
        }

    def apply_render_border(self, scene, x_min, x_max, y_min, y_max):
        scene.render.use_border = True
        scene.render.use_crop_to_border = False
        scene.render.border_min_x = x_min
        scene.render.border_max_x = x_max
        scene.render.border_min_y = y_min
        scene.render.border_max_y = y_max
        
        # Lower samples for quick benchmarking
        if scene.render.engine == 'CYCLES':
            scene.cycles.samples = 16
        else:
            try:
                scene.eevee.taa_render_samples = 16
            except AttributeError:
                pass

    def render_sample(self):
        """Synchronous render of the current border region. Returns wall-clock seconds."""
        start_time = time.time()
        bpy.ops.render.render(write_still=False)
        return time.time() - start_time

    def restore_settings(self, scene):
        if not self.original_settings:
            return
            
        scene.render.use_border = self.original_settings["use_border"]
        scene.render.border_min_x = self.original_settings["border_min_x"]
        scene.render.border_max_x = self.original_settings["border_max_x"]
        scene.render.border_min_y = self.original_settings["border_min_y"]
        scene.render.border_max_y = self.original_settings["border_max_y"]
        scene.render.use_crop_to_border = self.original_settings["use_crop_to_border"]
        
        if scene.render.engine == 'CYCLES':
            scene.cycles.samples = self.original_settings["samples"]
        else:
            try:
                scene.eevee.taa_render_samples = self.original_settings["samples"]
            except AttributeError:
                pass
