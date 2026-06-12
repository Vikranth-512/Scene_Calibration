import bpy
from ..utils.statistics import SceneAnalysisSnapshot
from ..analyzers.hardware_analyzer import analyze_hardware
from ..analyzers.scene_analyzer import analyze_scene
from ..analyzers.mesh_analyzer import analyze_meshes
from ..analyzers.texture_analyzer import analyze_textures
from ..analyzers.material_analyzer import analyze_materials
from ..analyzers.lighting_analyzer import analyze_lighting
from ..analyzers.volume_analyzer import analyze_volumes
from ..analyzers.render_settings_analyzer import analyze_render_settings
from ..estimation.complexity_score import calculate_scores
from ..estimation.render_time_estimator import RuleBasedEstimator

class RENDERANALYZER_OT_analyze_animation(bpy.types.Operator):
    """Analyze animation over multiple frames"""
    bl_idname = "renderanalyzer.analyze_animation"
    bl_label = "Analyze Animation"
    
    _timer = None
    _current_frame = 0
    _end_frame = 0
    _step = 1
    
    _sampled_frames = []
    _sampled_times = []
    
    _state = 'INIT'
    _snapshot = None
    _static_data = None
    _depsgraph = None
    _meshes = None
    _instances = None
    
    def modal(self, context, event):
        if event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if self._state == 'INIT':
                # Cache static invariant data once
                self._static_data = {
                    'hardware': analyze_hardware(),
                    'materials': analyze_materials(scene=context.scene),
                    'top_textures': analyze_textures(),
                    'render_settings': analyze_render_settings()
                }
                self._state = 'FRAME_SET'
                return {'PASS_THROUGH'}
                
            elif self._state == 'FRAME_SET':
                if self._current_frame > self._end_frame:
                    self._state = 'COMPLETE'
                else:
                    context.scene.frame_set(self._current_frame)
                    self._state = 'DEPSGRAPH_READY'
                return {'PASS_THROUGH'}
                
            elif self._state == 'DEPSGRAPH_READY':
                # Allow one tick for Blender to actually evaluate the frame change
                self._depsgraph = context.evaluated_depsgraph_get()
                self._state = 'MESH_ANALYSIS'
                return {'PASS_THROUGH'}
                
            elif self._state == 'MESH_ANALYSIS':
                self._snapshot = SceneAnalysisSnapshot()
                
                # Restore static data
                self._snapshot.hardware = self._static_data['hardware']
                self._snapshot.top_textures = self._static_data['top_textures']
                self._snapshot.render_settings = self._static_data['render_settings']
                
                # Analyze per-frame dynamic data
                self._snapshot.scene_stats = analyze_scene(depsgraph=self._depsgraph)
                mode = context.scene.render_analyzer_props.analysis_mode
                self._meshes, self._instances = analyze_meshes(self._depsgraph, mode=mode)
                self._snapshot.instances = self._instances
                
                self._state = 'SCORING'
                return {'PASS_THROUGH'}
                
            elif self._state == 'SCORING':
                lighting = analyze_lighting(depsgraph=self._depsgraph)
                volumes = analyze_volumes(depsgraph=self._depsgraph)
                materials = self._static_data['materials']
                
                cycles_score, eevee_score, top_bottlenecks = calculate_scores(
                    self._meshes, self._instances, materials, lighting, 
                    volumes, self._snapshot.render_settings, instance_multiplier=0.15
                )
                
                self._snapshot.cycles_score = cycles_score
                self._snapshot.eevee_score = eevee_score
                self._snapshot.top_bottlenecks = top_bottlenecks
                
                self._state = 'STORE_RESULT'
                return {'PASS_THROUGH'}
                
            elif self._state == 'STORE_RESULT':
                benchmark_data = context.scene.render_analyzer_props.benchmark_data
                estimator = RuleBasedEstimator()
                est_result = estimator.estimate(self._snapshot, benchmark_data_json=benchmark_data)
                
                self._sampled_frames.append(self._current_frame)
                self._sampled_times.append(est_result.estimated_frame_time_seconds)
                
                self._state = 'NEXT_FRAME'
                
                # Redraw UI progressively
                for window in context.window_manager.windows:
                    for area in window.screen.areas:
                        area.tag_redraw()
                return {'PASS_THROUGH'}
                
            elif self._state == 'NEXT_FRAME':
                self._current_frame += self._step
                self._state = 'FRAME_SET'
                return {'PASS_THROUGH'}
                
            elif self._state == 'COMPLETE':
                self.finish(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        scene = context.scene
        self._current_frame = scene.frame_start
        self._end_frame = scene.frame_end
        self._sampled_frames = []
        self._sampled_times = []
        
        # Sample every N frames
        sample_count = 10
        total_frames = max(1, self._end_frame - self._current_frame)
        self._step = max(1, total_frames // sample_count)
        
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        self.report({'INFO'}, "Starting Animation Analysis...")
        return {'RUNNING_MODAL'}

    def finish(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        
        if not self._sampled_times:
            self.report({'WARNING'}, "No frames sampled.")
            return

        # Discrete Interpolation
        try:
            import numpy as np
            all_frames = np.arange(context.scene.frame_start, self._end_frame + 1)
            interpolated_times = np.interp(all_frames, self._sampled_frames, self._sampled_times)
            total_time = float(np.sum(interpolated_times))
        except ImportError:
            # Fallback if numpy missing
            avg_time = sum(self._sampled_times) / len(self._sampled_times)
            total_time = avg_time * (self._end_frame - context.scene.frame_start + 1)
            
        context.scene.render_analyzer_props.estimated_animation_time_s = total_time
        context.scene.frame_set(context.scene.frame_start)
        
        self.report({'INFO'}, f"Animation Analysis Complete. Total Est: {total_time/60.0:.1f} mins")

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        context.scene.frame_set(context.scene.frame_start)
        self.report({'WARNING'}, "Animation Analysis Cancelled")
