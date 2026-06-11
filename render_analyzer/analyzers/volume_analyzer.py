import bpy
from ..utils.statistics import VolumeStats

def analyze_volumes() -> VolumeStats:
    stats = VolumeStats()
    
    # Check for volume objects (domains etc)
    for obj in bpy.data.objects:
        if obj.type == 'VOLUME':
            stats.volume_count += 1
        elif obj.type == 'MESH':
            # Check if material has volumetric shaders
            has_volume = False
            for slot in obj.material_slots:
                mat = slot.material
                if mat and mat.use_nodes and mat.node_tree:
                    # Look for volume output connected
                    for link in mat.node_tree.links:
                        if link.to_socket.name == 'Volume' and link.to_node.type == 'OUTPUT_MATERIAL':
                            has_volume = True
                            break
            if has_volume:
                stats.volume_count += 1
                
    # Also check world volume
    world = bpy.context.scene.world
    if world and world.use_nodes and world.node_tree:
        for link in world.node_tree.links:
            if link.to_socket.name == 'Volume' and link.to_node.type == 'OUTPUT_WORLD':
                stats.volume_count += 1
                break

    stats.volumetric_cost_score = stats.volume_count * 100
    return stats
