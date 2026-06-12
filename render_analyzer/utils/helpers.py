import bpy
import hashlib
import json

def requires_depsgraph_evaluation(obj) -> bool:
    """Check if an object requires full depsgraph evaluation or can be used as-is. (Fixes P-06)"""
    # 1. Modifiers present
    if len(obj.modifiers) > 0:
        return True
        
    # 2. Shape keys present
    if hasattr(obj.data, "shape_keys") and obj.data.shape_keys:
        return True
        
    # 3. Instanced or shared mesh data
    if obj.is_from_instancer or (hasattr(obj.data, "users") and obj.data.users > 1):
        return True
        
    # 4. Driven properties
    if obj.animation_data and obj.animation_data.drivers:
        return True
        
    return False

def get_evaluated_mesh(obj, depsgraph):
    """Safely get an evaluated mesh for an object, skipping evaluation if possible."""
    if depsgraph is None:
        raise ValueError("Depsgraph must be explicitly provided.")
        
    if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
        return None
        
    # Fast path: if the mesh requires no evaluation, return base data
    if obj.type == 'MESH' and not requires_depsgraph_evaluation(obj):
        return obj.data
        
    obj_eval = obj.evaluated_get(depsgraph)
    
    try:
        # returns a new Mesh datablock
        mesh = obj_eval.to_mesh()
        return mesh
    except Exception:
        return None

def free_evaluated_mesh(obj_eval, mesh):
    """Free the evaluated mesh to prevent memory leaks. (Fixes L-01)"""
    if mesh is None:
        return
        
    # Safe check: if it's the original mesh from the fast path, DO NOT free it.
    if hasattr(obj_eval, "original") and obj_eval.original.data == mesh:
        return
        
    # If it is the original mesh without original pointer (fallback), don't free it.
    if getattr(obj_eval, "data", None) == mesh:
        return
        
    # In modern Blender (2.8+), obj_eval.to_mesh() creates an evaluated mesh 
    # owned by the object, which is freed using to_mesh_clear().
    # It does NOT reside in bpy.data.meshes, even if it shares the name of an existing mesh.
    try:
        if hasattr(obj_eval, 'to_mesh_clear'):
            obj_eval.to_mesh_clear()
            return
    except Exception:
        pass
        
    # Fallback for older Blender versions or manual mesh creation (e.g. bmesh.to_mesh())
    # Only remove if the exact mesh instance is in the database.
    try:
        if mesh in bpy.data.meshes.values():
            bpy.data.meshes.remove(mesh, do_unlink=True)
    except (ReferenceError, RuntimeError):
        pass

def generate_scene_fingerprint(scene=None):
    """Generates a secure SHA256 hash of the current scene state for cache invalidation. (Fixes C-01)"""
    if scene is None:
        scene = bpy.context.scene
        
    fingerprint = hashlib.sha256()
    
    # Render settings
    render = scene.render
    cycles = scene.cycles
    eevee = getattr(scene, 'eevee', None)
    
    engine = str(render.engine).encode('utf-8')
    res_x = str(render.resolution_x).encode('utf-8')
    res_y = str(render.resolution_y).encode('utf-8')
    samples = str(cycles.samples if render.engine == 'CYCLES' else getattr(eevee, "taa_render_samples", 64)).encode('utf-8')
    
    fingerprint.update(engine)
    fingerprint.update(res_x)
    fingerprint.update(res_y)
    fingerprint.update(samples)
    
    # World
    if scene.world:
        fingerprint.update(scene.world.name.encode('utf-8'))
        
    # Objects (Lightweight stats)
    for obj in bpy.data.objects:
        if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            fingerprint.update(obj.name.encode('utf-8'))
            fingerprint.update(obj.type.encode('utf-8'))
            if obj.data:
                # Fast base approximations without full evaluation
                fingerprint.update(str(len(obj.data.vertices)).encode('utf-8'))
                fingerprint.update(str(len(obj.data.polygons)).encode('utf-8'))
            fingerprint.update(str(len(obj.modifiers)).encode('utf-8'))
            fingerprint.update(str(len(obj.material_slots)).encode('utf-8'))
            
    # Materials
    for mat in bpy.data.materials:
        fingerprint.update(mat.name.encode('utf-8'))
        if mat.use_nodes and mat.node_tree:
            fingerprint.update(str(len(mat.node_tree.nodes)).encode('utf-8'))
            fingerprint.update(str(len(mat.node_tree.links)).encode('utf-8'))
            
    return fingerprint.hexdigest()
