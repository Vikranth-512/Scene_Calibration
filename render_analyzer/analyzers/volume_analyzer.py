import bpy
import math
import mathutils
from ..utils.statistics import VolumeStats

def analyze_volumes(depsgraph=None) -> VolumeStats:
    stats = VolumeStats()
    cost_accumulator = 0.0
    
    # Check for volume objects (domains etc)
    for obj in bpy.data.objects:
        is_volume = False
        if obj.type == 'VOLUME':
            is_volume = True
        elif obj.type == 'MESH':
            # Check if material has volumetric shaders
            for slot in obj.material_slots:
                mat = slot.material
                if mat and mat.use_nodes and mat.node_tree:
                    # Look for volume output connected
                    for link in mat.node_tree.links:
                        if link.to_socket.name == 'Volume' and link.to_node.type == 'OUTPUT_MATERIAL':
                            is_volume = True
                            break
                            
        if is_volume:
            stats.volume_count += 1
            vol = 1.0
            if obj.bound_box:
                min_v = mathutils.Vector((float('inf'), float('inf'), float('inf')))
                max_v = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))
                for v in obj.bound_box:
                    vw = obj.matrix_world @ mathutils.Vector(v)
                    min_v.x, min_v.y, min_v.z = min(min_v.x, vw.x), min(min_v.y, vw.y), min(min_v.z, vw.z)
                    max_v.x, max_v.y, max_v.z = max(max_v.x, vw.x), max(max_v.y, vw.y), max(max_v.z, vw.z)
                vol = abs((max_v.x - min_v.x) * (max_v.y - min_v.y) * (max_v.z - min_v.z))
                
            density = 1.0
            step_rate = 1.0
            if obj.type == 'VOLUME' and obj.data and hasattr(obj.data, 'step_size'):
                step_rate = 1.0 / max(0.001, obj.data.step_size)
                
            cost_accumulator += math.log1p(vol) * density * step_rate
                
    # Also check world volume
    world = bpy.context.scene.world
    if world and world.use_nodes and world.node_tree:
        for link in world.node_tree.links:
            if link.to_socket.name == 'Volume' and link.to_node.type == 'OUTPUT_WORLD':
                stats.volume_count += 1
                cost_accumulator += 50.0 # Standard heavy penalty for World volumes
                break

    stats.volumetric_cost_score = int(cost_accumulator * 10)
    return stats
