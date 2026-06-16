import bpy
from ..utils.statistics import LightingStats

def analyze_lighting(depsgraph=None) -> LightingStats:
    stats = LightingStats()
    scene = bpy.context.scene
    
    energies = []

    # 1. Analyze lamps
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            light = obj.data
            if light.type == 'POINT':
                stats.point_lights += 1
            elif light.type == 'SUN':
                stats.sun_lights += 1
            elif light.type == 'AREA':
                stats.area_lights += 1
            elif light.type == 'SPOT':
                stats.spot_lights += 1
                
            if hasattr(light, "energy"):
                energies.append(light.energy)

            # Check shadow casting
            if getattr(light, "use_shadow", True):
                stats.shadow_casting_lights += 1
                
        # 2. Check emissive objects
        elif obj.type == 'MESH':
            has_emission = False
            for slot in obj.material_slots:
                mat = slot.material
                if mat and mat.use_nodes and mat.node_tree:
                    for node in mat.node_tree.nodes:
                        if node.type == 'EMISSION':
                            has_emission = True
                            break
                        # Principled can also be emissive, but we'll stick to basic check
            if has_emission:
                stats.emissive_objects += 1

    # 3. Check HDRI environment
    world = scene.world
    if world and world.use_nodes and world.node_tree:
        for node in world.node_tree.nodes:
            if node.type == 'TEX_ENVIRONMENT':
                stats.hdri_environment = True
                break
                
    # Energy aggregations
    if energies:
        stats.total_energy = sum(energies)
        stats.max_energy = max(energies)
        stats.mean_energy = stats.total_energy / len(energies)
    else:
        stats.total_energy = 0.0
        stats.max_energy = 0.0
        stats.mean_energy = 0.0

    # Lighting Cost calculation
    stats.lighting_cost_score = (stats.area_lights * 5 + 
                                 stats.spot_lights * 4 + 
                                 stats.point_lights * 2 + 
                                 stats.sun_lights * 3 +
                                 (20 if stats.hdri_environment else 0) +
                                 stats.emissive_objects * 5)
                                 
    return stats
