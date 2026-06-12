import bpy
import time
import json
import os
from ..utils.scene_cache import load_analysis_from_cache

_render_start_time = 0.0

@bpy.app.handlers.persistent
def render_pre_handler(scene, *args):
    global _render_start_time
    _render_start_time = time.time()

@bpy.app.handlers.persistent
def render_post_handler(scene, *args):
    global _render_start_time
    render_duration = time.time() - _render_start_time
    
    # Ignore instant/canceled renders
    if render_duration <= 0.5:
        return 
        
    snapshot = load_analysis_from_cache(scene)
    if not snapshot:
        return
        
    tensor_data = snapshot.to_tensor()
    if tensor_data is None:
        return
        
    # Create the supervised learning pair (Features -> Target)
    data = {
        "features": tensor_data.tolist(),
        "render_time_seconds": render_duration,
        "engine": scene.render.engine,
        "resolution_x": scene.render.resolution_x,
        "resolution_y": scene.render.resolution_y
    }
    
    # Store centrally in the User Profile (e.g. AppData/Roaming/Blender Foundation/...)
    # This prevents polluting the local .blend file directory and unifies the dataset.
    scripts_dir = bpy.utils.user_resource('SCRIPTS')
    ra_dir = os.path.join(scripts_dir, "RenderAnalyzer")
    if not os.path.exists(ra_dir):
        os.makedirs(ra_dir)
        
    file_path = os.path.join(ra_dir, "training_dataset.jsonl")
    try:
        with open(file_path, 'a') as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        print(f"Render Analyzer: Failed to write telemetry: {e}")

def register_telemetry():
    if render_pre_handler not in bpy.app.handlers.render_pre:
        bpy.app.handlers.render_pre.append(render_pre_handler)
    if render_post_handler not in bpy.app.handlers.render_post:
        bpy.app.handlers.render_post.append(render_post_handler)

def unregister_telemetry():
    if render_pre_handler in bpy.app.handlers.render_pre:
        bpy.app.handlers.render_pre.remove(render_pre_handler)
    if render_post_handler in bpy.app.handlers.render_post:
        bpy.app.handlers.render_post.remove(render_post_handler)
