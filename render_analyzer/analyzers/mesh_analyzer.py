import bpy
from typing import Tuple, List, Dict
from ..utils.statistics import MeshStats, InstanceStats
from ..utils.helpers import get_evaluated_mesh, free_evaluated_mesh

def analyze_meshes(depsgraph) -> Tuple[List[MeshStats], List[InstanceStats]]:
    mesh_stats_list = []
    
    instance_counts: Dict[str, int] = {}
    base_object_refs: Dict[str, bpy.types.Object] = {}
    
    evaluated_cache: Dict[str, MeshStats] = {}
    
    # 1. Traverse all object instances in the depsgraph
    for instance in depsgraph.object_instances:
        obj = instance.object
        
        # We only care about objects that can render as geometry
        if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            continue
            
        obj_name = obj.name
        
        # Count instances
        if instance.is_instance:
            instance_counts[obj_name] = instance_counts.get(obj_name, 0) + 1
            if obj_name not in base_object_refs:
                base_object_refs[obj_name] = obj
        
        # If we haven't evaluated this base object's geometry yet, do it now
        if obj_name not in evaluated_cache and not instance.is_instance:
            stats = MeshStats()
            stats.object_name = obj_name
            
            # Check modifiers
            stats.has_modifiers = len(obj.modifiers) > 0
            stats.has_subdivision = any(m.type == 'SUBSURF' for m in obj.modifiers)
            stats.has_geometry_nodes = any(m.type == 'NODES' for m in obj.modifiers)
            
            # Evaluate geometry
            mesh = get_evaluated_mesh(obj, depsgraph)
            if mesh:
                stats.vertex_count = len(mesh.vertices)
                stats.edge_count = len(mesh.edges)
                stats.face_count = len(mesh.polygons)
                
                # Count triangles and ngons
                tri_count = 0
                ngon_count = 0
                for poly in mesh.polygons:
                    nv = poly.loop_total
                    if nv == 3:
                        tri_count += 1
                    elif nv == 4:
                        tri_count += 2
                    else:
                        ngon_count += 1
                        tri_count += nv - 2
                        
                stats.triangle_count = tri_count
                stats.ngon_count = ngon_count
                
                free_evaluated_mesh(obj.evaluated_get(depsgraph), mesh)
            
            # Scoring logic will be handled later or here
            # Simple heuristic score for base geometry
            if stats.face_count > 500000:
                stats.complexity_score = "Extreme"
            elif stats.face_count > 100000:
                stats.complexity_score = "High"
            elif stats.face_count > 10000:
                stats.complexity_score = "Moderate"
            else:
                stats.complexity_score = "Low"
                
            evaluated_cache[obj_name] = stats
            mesh_stats_list.append(stats)

    # 2. Build InstanceStats
    instance_stats_list = []
    for name, count in instance_counts.items():
        i_stat = InstanceStats()
        i_stat.base_object_name = name
        i_stat.instance_count = count
        
        # Calculate total instanced faces if base object was evaluated
        if name in evaluated_cache:
            base_stats = evaluated_cache[name]
            i_stat.total_instanced_faces = base_stats.face_count * count
            # Tag the base stats as having instances
            base_stats.is_instanced = True
        else:
            # If base wasn't in the view layer directly but instanced
            obj = base_object_refs[name]
            mesh = get_evaluated_mesh(obj, depsgraph)
            faces = len(mesh.polygons) if mesh else 0
            i_stat.total_instanced_faces = faces * count
            if mesh:
                free_evaluated_mesh(obj.evaluated_get(depsgraph), mesh)
                
        instance_stats_list.append(i_stat)

    return mesh_stats_list, instance_stats_list
