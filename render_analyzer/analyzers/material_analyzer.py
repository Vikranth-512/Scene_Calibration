import bpy
from typing import List
from ..utils.statistics import MaterialStats

def analyze_materials(scene=None) -> List[MaterialStats]:
    results = []
    
    if scene is None:
        scene = bpy.context.scene
        
    scene_materials = set()
    for obj in scene.objects:
        if hasattr(obj, 'material_slots'):
            for slot in obj.material_slots:
                if slot.material:
                    scene_materials.add(slot.material)
    
    for mat in scene_materials:
        stats = MaterialStats(name=mat.name)
        
        if not mat.use_nodes or not mat.node_tree:
            results.append(stats)
            continue
            
        nodes = mat.node_tree.nodes
        for node in nodes:
            ntype = node.type
            if ntype == 'BSDF_PRINCIPLED':
                stats.principled_count += 1
            elif ntype in {'BSDF_GLASS', 'BSDF_TRANSPARENT', 'BSDF_REFRACTION'}:
                stats.glass_count += 1
            elif ntype == 'VOLUME_SCATTER':
                stats.volume_scatter_count += 1
            elif ntype == 'VOLUME_ABSORPTION':
                stats.volume_absorption_count += 1
            elif ntype == 'EMISSION':
                stats.emission_count += 1
            elif ntype == 'TEX_NOISE':
                stats.noise_count += 1
            elif ntype == 'TEX_VORONOI':
                stats.voronoi_count += 1
            elif ntype == 'TEX_MUSGRAVE':
                stats.musgrave_count += 1
            elif ntype == 'TEX_WAVE':
                stats.wave_count += 1
            elif ntype == 'MIX_SHADER':
                stats.mix_shader_count += 1
            elif ntype == 'MIX_RGB':
                stats.mix_rgb_count += 1
            elif ntype == 'DISPLACEMENT':
                stats.displacement_count += 1
            elif ntype == 'BUMP':
                stats.bump_count += 1
            elif ntype == 'NORMAL_MAP':
                stats.normal_map_count += 1
                
        # Calculate shader complexity score
        # Weighting:
        # Volumetric = 50, Glass/Refraction = 20, Displacement = 15, Procedurals = 5
        score = (stats.volume_scatter_count * 50 +
                 stats.volume_absorption_count * 30 +
                 stats.glass_count * 20 +
                 stats.displacement_count * 15 +
                 (stats.noise_count + stats.voronoi_count + stats.musgrave_count + stats.wave_count) * 5 +
                 stats.principled_count * 2)
                 
        stats.shader_complexity_score = score
        results.append(stats)
        
    # Sort by complexity descending
    results.sort(key=lambda x: x.shader_complexity_score, reverse=True)
    return results
