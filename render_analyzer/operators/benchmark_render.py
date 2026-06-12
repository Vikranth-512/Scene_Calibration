import bpy
import json
import os
import subprocess
import tempfile
import uuid

class RENDERANALYZER_OT_benchmark_render(bpy.types.Operator):
    """Run a border-region benchmark to estimate render times"""
    bl_idname = "renderanalyzer.benchmark_render"
    bl_label = "Benchmark Render"
    
    _timer = None
    _process = None
    _temp_blend = None
    _temp_json = None

    def modal(self, context, event):
        if event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if self._process is None:
                self.finish_cleanup(context)
                return {'CANCELLED'}
                
            retcode = self._process.poll()
            
            if retcode is not None:
                # Process finished
                if retcode == 0 and os.path.exists(self._temp_json):
                    try:
                        with open(self._temp_json, 'r') as f:
                            results = json.load(f)
                            
                        if not results:
                            self.report({'ERROR'}, "Benchmark produced no results.")
                        else:
                            props = context.scene.render_analyzer_props
                            props.last_benchmark_time = sum(r['time'] for r in results) / len(results)
                            props.benchmark_data = json.dumps(results)
                            
                            bpy.ops.renderanalyzer.analyze_scene()
                            self.report({'INFO'}, f"Benchmark Complete. Captured {len(results)} progressive samples.")
                    except Exception as e:
                        self.report({'ERROR'}, f"Failed to parse benchmark results: {e}")
                else:
                    self.report({'ERROR'}, "Benchmark failed or was interrupted.")
                    
                self.finish_cleanup(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        if self._process is not None:
            self.report({'WARNING'}, "Benchmark already running.")
            return {'CANCELLED'}
            
        scene = context.scene
        
        # We need to save a copy of the current state for the background process
        temp_dir = tempfile.gettempdir()
        job_id = str(uuid.uuid4())
        self._temp_blend = os.path.join(temp_dir, f"benchmark_job_{job_id}.blend")
        self._temp_json = os.path.join(temp_dir, f"benchmark_job_{job_id}.json")
        
        try:
            bpy.ops.wm.save_as_mainfile(filepath=self._temp_blend, copy=True)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save temp blend file: {e}")
            return {'CANCELLED'}
            
        # Get path to benchmark_worker.py
        addon_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        worker_script = os.path.join(addon_dir, "benchmark", "benchmark_worker.py")
        
        blender_exe = bpy.app.binary_path
        
        cmd = [
            blender_exe,
            "-b", self._temp_blend,
            "-P", worker_script,
            "--", self._temp_json
        ]
        
        try:
            self._process = subprocess.Popen(cmd)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to launch background process: {e}")
            self.finish_cleanup(context)
            return {'CANCELLED'}
            
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        
        self.report({'INFO'}, "Starting Background Benchmark...")
        return {'RUNNING_MODAL'}

    def finish_cleanup(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
            
        self._process = None
        
        if self._temp_blend and os.path.exists(self._temp_blend):
            try: os.remove(self._temp_blend)
            except: pass
            
        if self._temp_json and os.path.exists(self._temp_json):
            try: os.remove(self._temp_json)
            except: pass

    def cancel(self, context):
        if self._process:
            self._process.terminate()
            self._process = None
            
        self.finish_cleanup(context)
        self.report({'WARNING'}, "Benchmark Cancelled")

