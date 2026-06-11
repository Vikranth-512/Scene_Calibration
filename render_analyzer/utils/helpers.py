import bpy
import hashlib
import json

def get_evaluated_mesh(obj, depsgraph=None):
    """Safely get an evaluated mesh for an object."""
    if depsgraph is None:
        depsgraph = bpy.context.evaluated_depsgraph_get()
    
    obj_eval = obj.evaluated_get(depsgraph)
    
    # Check if object has geometry data
    if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
        return None
        
    try:
        # returns a new Mesh datablock
        mesh = obj_eval.to_mesh()
        return mesh
    except Exception:
        return None

def free_evaluated_mesh(obj_eval, mesh):
    """Free the evaluated mesh to prevent memory leaks."""
    if mesh is not None and hasattr(obj_eval, 'to_mesh_clear'):
        obj_eval.to_mesh_clear()

def generate_scene_fingerprint(scene=None):
    """Generates a hash of the current scene state for cache invalidation."""
    if scene is None:
        scene = bpy.context.scene
        
    # Factors that change the analysis
    data_points = [
        str(len(bpy.data.objects)),
        str(len(bpy.data.materials)),
        str(len(bpy.data.images)),
        str(len(bpy.data.lights)),
        str(scene.frame_current),
        str(scene.render.engine),
        str(scene.render.resolution_x),
        str(scene.render.resolution_y),
        str(scene.render.resolution_percentage),
        str(scene.cycles.samples if scene.render.engine == 'CYCLES' else scene.eevee.taa_render_samples)
    ]
    
    fingerprint_str = "|".join(data_points)
    return hashlib.md5(fingerprint_str.encode('utf-8')).hexdigest()
