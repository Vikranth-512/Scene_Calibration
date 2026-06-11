import bpy
from mathutils import Vector
from ..utils.statistics import SceneStats

def analyze_scene() -> SceneStats:
    stats = SceneStats()
    scene = bpy.context.scene
    
    stats.total_objects = len(bpy.data.objects)
    stats.materials = len(bpy.data.materials)
    stats.textures = len(bpy.data.images)
    stats.collections = len(bpy.data.collections)
    
    min_b = Vector((float('inf'), float('inf'), float('inf')))
    max_b = Vector((float('-inf'), float('-inf'), float('-inf')))
    valid_bounds = False

    for obj in scene.objects:
        if obj.hide_render or obj.hide_viewport:
            stats.hidden_objects += 1
        else:
            stats.visible_objects += 1
            
        t = obj.type
        if t == 'MESH':
            stats.meshes += 1
            # Simple base mesh counts without depsgraph (for high-level stats)
            if obj.data:
                stats.total_vertices += len(obj.data.vertices)
                stats.total_edges += len(obj.data.edges)
                stats.total_faces += len(obj.data.polygons)
        elif t == 'LIGHT':
            stats.lights += 1
        elif t == 'CAMERA':
            stats.cameras += 1
        elif t == 'CURVE':
            stats.curves += 1
        elif t == 'VOLUME':
            stats.volumes += 1

        # Particle Systems
        stats.particle_systems += len(obj.particle_systems)
        
        # Bounding box calculation for the scene extent
        if obj.bound_box and obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            for v in obj.bound_box:
                v_world = obj.matrix_world @ Vector(v)
                min_b.x = min(min_b.x, v_world.x)
                min_b.y = min(min_b.y, v_world.y)
                min_b.z = min(min_b.z, v_world.z)
                max_b.x = max(max_b.x, v_world.x)
                max_b.y = max(max_b.y, v_world.y)
                max_b.z = max(max_b.z, v_world.z)
                valid_bounds = True
                
    if valid_bounds:
        stats.bounds_min = (min_b.x, min_b.y, min_b.z)
        stats.bounds_max = (max_b.x, max_b.y, max_b.z)

    return stats
